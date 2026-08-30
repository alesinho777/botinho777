# Botinho777

Asistente de análisis de fútbol (motor Poisson). El producto principal hoy
es la **app web** (`src/webapp/`); el bot de Telegram (`src/bot/`) quedó
armado pero en pausa. Ver `BOTINHO777_SPEC_CLAUDE_CODE.md` para la
especificación completa.

No es casa de apuestas. No garantiza resultados. Análisis, no consejo de apuesta.

Estado actual: motor Poisson con corrección Dixon-Coles, `markets.py`,
ratings desde CSV, CLI de predicción, renderer sin LLM, snapshot/settle/
`/historial`, y la app web con login, tope free/premium manual y chat con
LLM sobre el partido consultado. El bot de Telegram mínimo (sección 16,
pasos 1–6 y 8 del spec) sigue en el repo pero no es el canal activo.

## Instalar

```bash
python -m pip install -e .
python -m pip install -e ".[dev]"   # para correr los tests
```

## Cargar datos

El repo trae un CSV sintético de ejemplo (una liga de demostración `DEMO`,
10 equipos, 3 temporadas) para poder correr todo offline:

```
data/raw/demo_matches.csv
```

Se generó con `scripts/generate_demo_csv.py` (no representa una liga real).
Para usar tu propio historial, dale el mismo formato de columnas:

```
date,competition_id,season,home_team_id,away_team_id,home_goals,away_goals
```

## Correr `predict`

```bash
python -m src.model.predict --home demo_team_01 --away demo_team_02
python -m src.model.predict --home demo_team_01 --away demo_team_02 \
    --csv data/raw/demo_matches.csv --competition DEMO
```

Devuelve el JSON de predicción (schema en `src/model/schemas.py`): lambdas,
mercados 1X2/BTTS/O-U/marcador exacto derivados de la misma matriz de
Poisson, factores y nivel de confianza.

### Dixon-Coles (fase 1.5, sección 11.5 del spec)

Poisson independiente subestima 0-0/1-1 y sobrestima 1-0/0-1. Encima de las
ratings att/def/home_adv (Opción A, sin cambios) se ajusta un único
parámetro `rho` por liga que corrige esos 4 marcadores, por máxima
verosimilitud sobre el mismo historial ya filtrado por fecha
(`src/data/features.py::_estimate_rho`, aplicado en
`src/model/poisson.py::score_matrix`). Con datos insuficientes cae a
`rho=0.0` (sin corrección) en vez de romper o inventar un ajuste. Esto
**no** reemplaza la necesidad de comparar contra baselines (sección 11.10:
"siempre local", "siempre favorito de cuota") antes de asumir que el
modelo agrega valor real — eso sigue pendiente.

## Tests

```bash
python -m pytest -q
```

Cubren que las probabilidades de cada mercado sumen 1 y el ejemplo numérico
River–Boca de la sección 11.8 del spec (lambdas fijos de calibración).

## Renderer (sin LLM)

`src/nlp/render.py` toma el JSON del motor y arma el texto de paquete
(sección 9.7), con el tono de Botinho777 y el disclaimer corto al final.
No usa ningún LLM.

## Demo web (Streamlit): app, no bot

Producto 100% web (sin depender de Telegram): login con email + contraseña,
tope free diario y rol premium manual, y el mismo paquete de siempre
(1X2 + BTTS + O/U + top marcadores) armado por `predict` + `render`, con el
disclaimer al pie. No toca el motor, solo lo llama. Técnicamente esto ya no
es un "bot" (no hay agente conversacional automatizado): es una app web de
análisis, aunque mantenga el nombre Botinho777. Cobrar por acceso premium
sigue siendo el mismo modelo de negocio del spec (sección 1): la
restricción legal de Paraguay (sección 2) es sobre qué se vende —análisis,
no intermediar apuestas—, no sobre si el canal es Telegram o web.

```bash
python -m streamlit run src/webapp/app.py
```

Usá `python -m streamlit` (no el comando `streamlit` a secas): así Python
agrega la carpeta del proyecto al path y encuentra el paquete `src`. Con el
comando pelado a veces tira `ModuleNotFoundError: No module named 'src'`.

### Diseño

Tema verde-cancha/oscuro nativo de Streamlit en `.streamlit/config.toml`
como base, más un bloque de CSS propio inyectado en `_landing_page()`
(`src/webapp/app.py::_LANDING_CSS`) exclusivo para la landing pública:
navbar centrada con logo + links de ancla (`#como-funciona`, `#planes`,
`#historial`, `#faq`), hero con gradiente radial y texto animado
(`fade-up`), tarjetas (`.bt-card`) para el teaser del partido demo y para
cada plan, grilla de pasos "Cómo funciona" y de stats de "Historial", y
acordeón de preguntas frecuentes con `st.expander`. Nada de esto toca el
motor: es capa visual pura sobre los mismos datos de `predict`/`render`.
El resultado del paquete y el chat (ya logueado) van dentro de
`st.container(border=True)` para que se vean como tarjetas, no texto
plano — esa parte no usa el CSS de la landing.

La página de entrada es pública (no pide login de una): barra superior con
la marca y botones "Iniciar sesión"/"Registrarme" que abren un modal
(`st.dialog`), y debajo el teaser del partido de ejemplo, "Cómo funciona",
"Planes" (tarjetas Gratis/Premium armadas desde el mismo `PLANES_TEXT` del
bot), "Historial" (stats reales del backtest si `settlements.csv` tiene
datos, si no el texto honesto de `NO_HISTORIAL_TEXT`) y preguntas
frecuentes, todo visible sin cuenta. El paquete completo y el chat siguen
requiriendo login. "Olvidé mi contraseña" es un botón chico (`st.popover`)
dentro del modal de login, pidiendo el email una sola vez (no se repite en
el segundo paso). Deliberadamente **no** sigue el patrón visual de sitios
de apuestas (bonos, cuotas, cronómetros de oferta) — eso violaría la
sección 2 del spec.

### Cuentas, tope free y premium (habilitación manual)

- Registro/login viven en `src/webapp/auth.py`, con hash de password por
  `hashlib.pbkdf2_hmac` (sin librería externa de auth) guardado en SQLite
  (`DATABASE_PATH`, default `data/botinho.db`).
- El tope free diario (`MAX_FREE_QUERIES_PER_DAY` del `.env`) y el rol
  premium viven en `src/webapp/quota.py`. Al pasarse el tope se muestra el
  mismo texto del spec (sección 9.4) en vez de bloquear con un error.
- Para habilitar premium a mano después de que alguien pague por fuera
  (transferencia, etc.):

```bash
python scripts/grant_premium.py --email alguien@mail.com --days 30
```

La persona tiene que haberse registrado antes en la web con ese mismo
email.

### "Olvidé mi contraseña" (link por email, Gmail SMTP)

Al lado de la contraseña del login hay un link chico "¿Olvidaste tu
contraseña?": pedís el email y te llega un **link** (no un código para
copiar a mano) que abre una página aparte de la app
(`APP_BASE_URL` + `?reset_email=...&reset_token=...`) donde ponés la
contraseña nueva dos veces (nueva + confirmación) para evitar errores de
tipeo. El token vence a los 15 minutos y es de un solo uso, y se guarda
hasheado igual que la contraseña — nunca en texto plano. Para que funcione
hace falta una cuenta de Gmail con **contraseña de aplicación** (no tu
contraseña normal de Google — se genera en
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords),
requiere verificación en 2 pasos activada):

```
SMTP_USER=tu_cuenta@gmail.com
SMTP_APP_PASSWORD=la_contraseña_de_aplicación_de_16_dígitos
APP_BASE_URL=http://localhost:8501
```

`APP_BASE_URL` tiene que apuntar a donde esté corriendo la app de verdad
(cambialo si la publicás en otro dominio); si no se configura, asume
`http://localhost:8501`. Sin `SMTP_USER`/`SMTP_APP_PASSWORD` configurados,
la app avisa honestamente que todavía no puede mandar emails, en vez de
fallar en silencio.

### Chat con LLM (Modo B — narrator, sección 12 del spec)

Debajo del Paquete aparece un chat para preguntar libremente sobre ESE
partido ("¿por qué el local es favorito?", "¿qué tan confiable es el
pick?", etc.). El LLM **nunca calcula probabilidades**: solo recibe el
JSON que ya armó el motor Poisson y lo comenta, con el system prompt fijo
de `src/nlp/system_prompt.txt` (nunca "apuesta"/"está cantado"/"te
aseguro", nunca inventa un mercado que no vino en el JSON).

- Free: **3 preguntas por día** (`MAX_FREE_CHAT_QUESTIONS` del `.env`),
  con el mismo reset diario que el tope de paquetes. Al pasarse el tope
  muestra un aviso en vez de llamar al LLM.
- Premium (`grant_premium.py`): charla sin tope.
- Proveedor configurable por `.env` (nunca hardcodeado), sección 14 del
  spec:

```
LLM_PROVIDER=anthropic
LLM_API_KEY=tu_api_key_de_anthropic
LLM_MODEL=claude-haiku-4-5   # opcional, este es el default
```

Sin `LLM_API_KEY` configurada, el chat lo dice honestamente en vez de
romper la app o inventar una respuesta.

## Datos reales de ligas europeas (Champions, La Liga, Premier, Serie A)

Por ahora la carga de datos reales cubre estas 4 competiciones vía
[football-data.org](https://www.football-data.org) (API con plan gratuito).
Sudamérica (Libertadores, Sudamericana, Liga Argentina, Brasileirão) y la
liga paraguaya quedan pendientes: ese proveedor no las cubre en su plan
gratis, hace falta otra fuente (paga o un CSV que el usuario aporte).

1. Sacate una API key gratis en
   [football-data.org/client/register](https://www.football-data.org/client/register)
   y ponela en `.env`:

```
FOOTBALL_DATA_API_KEY=tu_api_key
```

2. Corré el script de carga (baja partidos terminados de las últimas 3
   temporadas por default, respetando el límite de 10 requests/min del plan
   free):

```bash
python -m scripts.fetch_real_data
python -m scripts.fetch_real_data --competitions CL PL   # solo algunas ligas
```

(Igual que con `predict`, usá `python -m` y no el archivo pelado, para que
Python encuentre el paquete `src`.)

Esto arma `data/raw/real_matches.csv` con el mismo formato que usa el motor
(`date,competition_id,season,home_team_id,away_team_id,home_goals,away_goals`),
mapeando los códigos de football-data.org a ids internos: `CL`→`CHAMPIONS`,
`PD`→`LALIGA`, `PL`→`PREMIER`, `SA`→`SERIEA`.

3. Una vez que `data/raw/real_matches.csv` existe con datos, la web
   (`src/webapp/app.py::_pick_data_source`) lo detecta solo y reemplaza la
   liga demo: aparece un selector de competición y los equipos reales de
   cada liga. Sin ese archivo (o si el plan free no te dejó bajar ninguna
   temporada), la app sigue mostrando la liga `DEMO` con un aviso, en vez de
   fallar. El plan gratuito de football-data.org tiene límites de acceso a
   temporadas históricas según la competición — si algún año no baja, el
   script lo indica y sigue con el resto.

### Calendario real (partidos de hoy, próximos días, semana y mes)

`real_matches.csv` es el **historial** (partidos ya jugados, para calcular
ratings) — para elegir un partido de verdad hace falta además el
**calendario** de partidos programados. Se baja aparte con:

```bash
python -m scripts.fetch_fixtures
python -m scripts.fetch_fixtures --days 14   # solo las próximas 2 semanas
```

Usa la misma `FOOTBALL_DATA_API_KEY` y arma `data/raw/upcoming_fixtures.csv`
(por default trae los próximos 35 días, o sea "hoy", "próximos días",
"la semana" y "el mes" quedan cubiertos con una sola corrida). En la web,
`_paquete_form` reemplaza los selectores libres de "Local"/"Visita" por un
único selector de **Partido** con la fecha y hora en horario de Paraguay
(`08/09 13:45 · Club Brugge KV vs Aston Villa FC`, por ejemplo), y arma la
predicción con `src/eval/snapshot.py::build_snapshot` usando como corte
(`as_of`) la fecha real del partido — o sea, solo mira historial anterior a
ese partido, igual que en el backtest, sin mirar resultados que todavía no
pasaron. Si no hay calendario cargado para una competición (o el plan free
no devolvió partidos programados), cae al selector manual de equipos como
antes, en vez de romper.

Como football-data.org no vende el calendario indefinidamente hacia
adelante, conviene volver a correr `fetch_fixtures` cada tanto (por ejemplo,
una vez por semana) para que la lista de próximos partidos no quede vieja.

### Nombres reales de equipo (no el id interno)

El motor identifica cada equipo con un id tipo slug (`fc_barcelona`,
`club_brugge_kv`) — hace falta para las ratings, pero se ve feo en pantalla.
Tanto `fetch_real_data.py` como `fetch_fixtures.py` ahora guardan también el
nombre real de cada equipo (columnas `*_team_name`) tal cual lo devuelve
football-data.org. La web (`src/webapp/app.py::_prettify_prediction`) arma
un mapa id→nombre con esos dos CSV y reemplaza el id por el nombre real en
el título del paquete y en cada factor ("Club Brugge KV tiene mejor ataque
suavizado que Aston Villa FC...") antes de mostrarlo o mandarlo al chat —
es un cambio de presentación nomás, no toca ningún cálculo del motor. Si un
equipo no tiene nombre cacheado (por ejemplo los equipos de la liga demo),
cae a un título legible armado a partir del id (`demo_team_01` →
"Demo Team 01") en vez de mostrar el id crudo.

## Snapshot + settle + `/historial`

`src/eval/snapshot.py` arma el JSON de predicción con un `as_of` explícito
(solo partidos anteriores a esa fecha, sin mirar el futuro) y lo guarda en
`data/predictions/YYYY-MM-DD.json`. `src/eval/settle.py` compara ese
snapshot contra el resultado real y agrega la fila a
`data/results/settlements.csv`. `src/eval/historial.py` agrega esos
settlements en el texto público de `/historial` — si todavía no hay datos,
lo dice en vez de inventar un porcentaje.

Como todavía no hay fixtures reales, `src/eval/backtest.py` genera un
backtest ilustrativo sobre partidos ya jugados del CSV demo (cada uno
predicho con el historial *anterior* a esa fecha, para no hacer trampa):

```bash
python -m src.eval.backtest --n 30
```

Imprime cuántos partidos liquidó y el texto de `/historial` resultante.

## Bot de Telegram

Bot mínimo en modo polling: `/start` con el copy y menú del spec, un
partido de demostración (`demo_team_01` vs `demo_team_02`, los equipos del
CSV) cuyo botón "Paquete" corre `predict` + `render`, y `/historial` con el
hit-rate público de settlements. Todavía sin pagos, tope free ni roles/`grant`.

1. Copiá `.env.example` a `.env` y completá `TELEGRAM_BOT_TOKEN` con el
   token que te da @BotFather. El token nunca se hardcodea.
2. Corré:

```bash
python -m src.bot.main
```
