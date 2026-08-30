# Botinho777 — Especificación completa para Claude Code

Documento único para implementar el producto.  
Idioma de la app y del bot: **español (es-PY / rioplatense neutro, claro)**.  
Stack previsto: Python, Telegram Bot API, FastAPI opcional, pandas, scikit-learn y/o modelo Poisson.

Si estás leyendo esto como agente de código: implementá según este spec. No inventes mercados, ligas ni tono que no estén acá. No prometas ganancias. No tomes apuestas.

---

## 0. Qué es este proyecto (en una frase)

Asistente conversacional de **análisis de fútbol** que responde por Telegram.  
Un motor estadístico calcula probabilidades. Un LLM (o plantillas + LLM) traduce esos números a charla amable, educada y graciosa.

**No es una casa de apuestas. No intermedia apuestas. No garantiza resultados.**

Nombre: **Botinho777**  
Dueño / builder: Augusto (Paraguay). Monetización: suscripción al chat / canal premium.

---

## 1. Objetivo de negocio

Generar ingresos con:

1. Canal/bot gratis con pronósticos limitados.
2. Acceso premium (charla ilimitada + más mercados + más partidos).
3. Más adelante: contenido (TikTok/reels) que mande tráfico al bot.

Precio de referencia (ajustable):

- Semanal: 30.000–80.000 Gs
- Mensual: 120.000–250.000 Gs

Pagos MVP: Telegram Stars y/o transferencia local (indicada por el dueño).  
No implementar pasarela compleja en el primer corte si no hace falta: puede ser “pagás → te habilito el user_id”.

---

## 2. Restricción legal (Paraguay) — OBLIGATORIO

En Paraguay las apuestas deportivas están reguladas (CONAJZAR / DNIT). Hay concesión para **operar** apuestas. Organizar, explotar, comercializar o intermediar apuestas sin autorización es actividad no autorizada.

Botinho777 es **análisis / entretenimiento**.

### El bot NUNCA debe

- Pedir o recibir dinero para apostar en nombre del usuario.
- Decir “apuesta esto”, “está cantado”, “te aseguro que gana”.
- Prometer ROI, bankroll o “sistema infalible”.
- Actuar como casa de apuestas o tipster que cobra por “pick garantizado”.
- Incluir enlaces a operadores de apuestas no autorizados en Paraguay.

### El bot SÍ puede

- Dar probabilidades, contexto y “por qué”.
- Comparar mercados (1X2, BTTS, O/U, exacto).
- Mostrar historial de aciertos del **modelo** (transparencia).
- Decir “si alguien apuesta, que lo haga por su cuenta y solo con dinero que pueda perder”.

Toda respuesta de pronóstico termina (o el menú /start incluye) un disclaimer corto. Ver sección 10.

---

## 3. Competencias

### Lista objetivo (producto)

| Código interno | Competencia | Prioridad MVP |
|---|---|---|
| PY | Primera División Paraguay (Apertura/Clausura) | Fase 3 |
| LIB | Copa Libertadores | Fase 2 |
| BRA | Brasileirão Serie A | Fase 2 |
| ARG | Liga Profesional Argentina | Fase 2 |
| EPL | Premier League | Fase 1 (MVP) |
| EL1 | EFL League One | Fase 3 |
| ITA | Serie A Italia | Fase 1 (MVP) |
| ESP | La Liga | Fase 1 (MVP) |
| UCL | UEFA Champions League | Fase 1 (MVP) |

MVP de modelo y bot: **EPL, ESP, ITA, UCL**.  
El menú puede listar todas las ligas, pero si no hay modelo entrenado esa liga responde:

> “Todavía no tengo motor propio para esa liga. No te voy a inventar un número. Te aviso cuando entre.”

No alucinar fixtures ni lesionados.

---

## 4. Mercados que el producto vende

| Mercado | Código | Salida |
|---|---|---|
| 1X2 | `1x2` | P(H), P(D), P(A) |
| Ambos marcan | `btts` | P(sí), P(no) |
| Over/Under goles | `ou` | default 2.5; también 1.5 y 3.5; P(over), P(under) |
| Resultado exacto | `cs` | top 3 (o top 5) scorelines + probabilidad de cada uno |
| Goles de un equipo | `team_ou` | P(equipo marca > X) — extra, no bloquea el MVP |

El usuario puede pedir uno o el “paquete”.  
Comando / paquete default = `1x2 + btts + ou_2.5 + cs_top3`.

---

## 5. Marca y tono (crítico para el LLM)

Nombre: **Botinho777**

Personalidad:

- Amable
- Educado (usted no hace falta; tutear está bien: “te armo”, “mirá”)
- Gracioso liviano (una línea, no stand-up)
- Honesto cuando el partido está 50/50
- Nunca soberbio

### Ejemplos de voz (copiar este estilo)

Bien:

> “Buenas. Lo miré con calma. El modelo se inclina al local (48%), pero el empate no es decoración (26%).”

> “Over 2.5 está 51–49. Eso no es una revelación: es una moneda con saco y corbata.”

> “Resultado exacto es lotería. El 1-1 es el más probable y igual es minoría. Sirve de mapa, no de profecía.”

Mal (prohibido):

> “Mandale al local que está regalado.”
> “IA certifica victoria visitante.”
> “Si no apostás esto, no sabés nada.”

Si faltan datos: admitirlo. No rellenar con opinión de hincha.

---

## 6. Arquitectura (lo que Claude Code tiene que construir)

Tres capas. No mezclar.

```
[Usuario Telegram]
        |
        v
[Bot handler]  --parsea intención, liga, mercados--
        |
        +--> [Capa datos] fixtures, teams, results, features
        |
        +--> [Motor] Poisson/Dixon-Coles (+ opcional ML)
        |         devuelve JSON de probs
        |
        +--> [Capa respuesta] plantilla + LLM
                  solo puede hablar de lo que vino en el JSON
```

### Regla de oro del LLM

El modelo de lenguaje **no calcula** las probs.  
Recibe un JSON del motor y lo narra.  
Si el JSON no tiene un mercado, dice que no lo tiene.

### Stack sugerido

- Python 3.11+
- `python-telegram-bot` (v21+) o aiogram
- pandas, numpy
- scipy (poisson)
- scikit-learn (opcional, ratings / features)
- sqlite o parquet local para MVP
- pydantic para schemas
- pytest para el motor (las probs tienen que sumar ~1)

Estructura de repo sugerida:

```
botinho777/
  README.md
  pyproject.toml
  .env.example
  data/
    raw/
    processed/
    predictions/      # snapshots pre-partido
    results/          # settlement
  src/
    config.py
    data/
      ingest.py
      clean.py
      features.py
    model/
      ratings.py
      poisson.py
      markets.py
      train.py
      predict.py
    bot/
      main.py
      handlers.py
      keyboards.py
      copy.py
    nlp/
      intent.py
      render.py       # JSON -> texto Botinho
    eval/
      backtest.py
      settle.py
  tests/
    test_markets.py
    test_poisson_sums.py
```

---

## 7. Documento de producto Telegram

### 7.1 Comandos

| Comando | Qué hace |
|---|---|
| `/start` | Bienvenida + menú + disclaimer |
| `/hoy` | Partidos de hoy (ligas cubiertas) |
| `/manana` | Partidos de mañana |
| `/liga` | Elegir liga |
| `/partido` | Buscar por nombres de equipos |
| `/paquete` | 1X2 + BTTS + O/U 2.5 + exactos |
| `/1x2` `/btts` `/goles` `/exacto` | Un mercado |
| `/historial` | Hit-rate del modelo (público) |
| `/planes` | Precios y qué incluye cada plan |
| `/ayuda` | Cómo preguntar |
| `/disclaimer` | Texto legal corto |

También acepta lenguaje natural:

- “qué ves en city vs arsenal”
- “ambos marcan en el clásico?”
- “más de 2.5 en barcelona-girona”
- “resultado más probable real madrid vs sociedad”

### 7.2 Flujo /start (gratis)

1. Mensaje de bienvenida (ver 9.1)
2. Botones:
   - Partidos de hoy
   - Elegir liga
   - Cómo funciona
   - Plan premium
3. Límite free MVP (configurable):
   - 5 consultas de pronóstico por día por user_id
   - o 1 paquete completo por día
   - el resto: “llegaste al tope gratis de hoy. Con premium charlás sin techo.”

### 7.3 Menú inline (teclado)

Nivel 1 — Home  
`[Hoy] [Mañana] [Ligas] [Planes] [Historial]`

Nivel 2 — Ligas  
`[Premier] [La Liga] [Serie A] [Champions] [Más ligas]`

Nivel 3 — Partido  
Al elegir un fixture:

```
Cerro Porteño vs Olimpia
Dom 16:00 (hora PY)

[Paquete] [1X2] [Ambos marcan]
[Over/Under] [Exacto] [Otro partido]
```

Nivel 4 — Over/Under  
`[1.5] [2.5] [3.5]`

### 7.4 Estados del usuario (FSM simple)

`IDLE -> PICK_LEAGUE -> PICK_MATCH -> PICK_MARKET -> ANSWER`

Lenguaje natural puede saltar directo a ANSWER si se detectan dos equipos + mercado.

### 7.5 Roles

- `free`
- `premium` (hasta fecha `premium_until`)
- `admin` (el dueño: puede forzar settle, ver logs, habilitar users)

Tabla `users`: `telegram_id, role, premium_until, daily_count, last_reset_date`.

---

## 8. Detección de intención (NLP liviano)

No hace falta un LLM para parsear todo. Orden:

1. Regex / keywords: “ambos marcan”, “btts”, “más de 2.5”, “over”, “under”, “1x2”, “exacto”, “resultado correcto”
2. Matching de equipos (fuzzy: “barsa”, “oma”, “city”)
3. Si hay duda, preguntar con botones. No adivinar el partido equivocado.

Diccionario mínimo de aliases en `src/nlp/aliases.yml` (extensible):

```yaml
barcelona: ["barsa", "barça", "fcb"]
olimpia: ["oma", "decano"]
cerro_porteno: ["cerro", "cpc"]
manchester_city: ["city", "mancity"]
```

Si dos equipos matchean a más de un fixture en la ventana de 7 días: listar y que elija.

---

## 9. Textos de producto (copy listo para pegar)

### 9.1 /start

```
Buenas, soy Botinho777.

Te ayudo a leer partidos con números: 1X2, ambos marcan, más/menos goles y el marcador más probable.

No soy casa de apuestas y no te aseguro nada. El fútbol es un caos con césped. Yo traduzco un modelo estadístico a castellano, con humor y sin humo.

Probá con:
• /hoy
• “City vs Arsenal, paquete”
• /planes

Análisis. No garantía.
```

### 9.2 Cómo funciona

```
1) Miro historial y forma (goles a favor/en contra, localía).
2) El motor calcula probabilidades.
3) Te las cuento en cristiano.

Si el partido está 50/50, te lo digo. No vendo certeza falsa.
```

### 9.3 /planes

```
Gratis
• 5 consultas por día
• Paquete básico en ligas del MVP

Premium
• Charla sin tope
• 1.5 / 2.5 / 3.5
• Top marcadores
• Prioridad en fechas grandes (Champions, clásicos)

Precio de referencia
• Semanal: 50.000 Gs
• Mensual: 150.000 Gs

Escribime “quiero premium” y te paso cómo habilitarlo.

Sigue siendo análisis. Premium no convierte un empate en milagro.
```

### 9.4 Tope free

```
Llegaste al tope gratis de hoy. Mañana recargo el contador.

Si querés seguir charlando ahora: /planes
```

### 9.5 Liga aún no cubierta

```
Esa liga está en la lista del producto, pero el motor todavía no come esos datos. Preferible silencio a un número inventado.

MVP ahora: Premier, La Liga, Serie A y Champions.
```

### 9.6 Partido no encontrado

```
No ubico ese cruce en los próximos 7 días (o no está en mis ligas).
Probá /hoy o escribí los dos nombres un poco más claros.
```

### 9.7 Plantilla de respuesta PAQUETE (el LLM o el renderer debe seguir este esqueleto)

```
{saludo_corto}

*{home} vs {away}*
{competition} · {kickoff_local_py}

*1X2*
Local: {p_h:.0%}
Empate: {p_d:.0%}
Visita: {p_a:.0%}
{one_liner_1x2}

*Ambos marcan*
Sí {p_btts_yes:.0%} · No {p_btts_no:.0%}
{one_liner_btts}

*Goles (línea {line})*
Más de {line}: {p_over:.0%}
Menos de {line}: {p_under:.0%}
{one_liner_ou}

*Marcadores más probables*
1) {s1} ({p1:.0%})
2) {s2} ({p2:.0%})
3) {s3} ({p3:.0%})
Exacto es lotería: el primero igual suele ser minoría.

Confianza: {low|media|alta}
Por qué: {2-3 factores del JSON, nada inventado}

Análisis del modelo. No es una garantía.
```

`confianza` sale del motor, no del LLM:

- alta: max(P_H, P_D, P_A) ≥ 0.55 y |λ_h − λ_a| ≥ 0.6
- baja: max < 0.40 o |λ_h − λ_a| < 0.25
- si no: media

### 9.8 Texto corto para canal gratis (broadcast)

```
📅 {fecha}
{home} vs {away} ({liga})

1X2  {h:.0%} / {d:.0%} / {a:.0%}
BTTS sí {btts:.0%}
O/U 2.5  over {over:.0%}

Más detalle en el bot: @Botinho777bot
Análisis, no garantía.
```

---

## 10. Disclaimer (usar siempre)

Corto (al pie de pronósticos):

```
Análisis estadístico con fines informativos. No es consejo de apuesta ni garantía de resultado. +18. Jugá con cabeza, o ni juegues.
```

Largo (`/disclaimer`):

```
Botinho777 publica probabilidades estimadas por un modelo a partir de resultados históricos y forma reciente.

El fútbol tiene lesiones, árbitros, clima y noches raras. Una probabilidad de 55% significa que, en 100 mundos parecidos, unas 55 veces sale ese lado. Las otras 45 también existen.

No operamos apuestas. No recibimos dinero para apostar por vos. No nos asociamos a casas sin autorización en Paraguay.

Si alguien decide apostar, es bajo su responsabilidad y solo con dinero que pueda perder. El juego puede generar dependencia. Si sentís que se te fue de las manos, buscá ayuda.
```

---

## 11. Diseño del modelo (motor)

### 11.1 Idea

No predecir 1X2 “a ojo” con un clasificador suelto como única fuente.  
Primero estimar **goles esperados** de cada equipo (λ_home, λ_away).  
Después derivar TODOS los mercados de la misma matriz de marcadores.  
Así 1X2, BTTS, O/U y exacto son **consistentes entre sí**.

Modelo base MVP: **Poisson independiente**.  
Mejora inmediata: **Dixon-Coles** (corrige empates 0-0 y 1-1, típicos en fútbol).

Opcional fase 2: gradient boosting que predice λ o que predice 1X2, y se mezcla (ensemble). No empezar por ahí.

### 11.2 Datos de entrada (partidos históricos)

Una fila = un partido ya jugado.

Columnas mínimas:

```
date                datetime
competition_id      str
season              str
home_team_id        str
away_team_id        str
home_goals          int
away_goals          int
```

Columnas útiles si existen:

```
home_xg, away_xg
home_shots, away_shots
odds_h, odds_d, odds_a     # solo como feature / baseline, no como verdad
```

Fixtures futuros (para predecir):

```
date, competition_id, home_team_id, away_team_id, kickoff
```

IDs de equipos estables. Normalizar nombres (“Cerro Porteño” vs “Cerro Porteno”).

Fuentes sugeridas (el implementador elige según API key disponible):

- football-data.co.uk (EPL, La Liga, Serie A, Championship/League One; CSV gratis)
- API-Football / Football-Data.org (fixtures + stats; hay free tier)
- openfootball / datasets públicos para Sudamérica cuando el CSV europeo no alcanza

Paraguay y Libertadores: ingesta aparte. Si no hay historial suficiente, no forzar el modelo.

### 11.3 Features / ratings (lo que “come” el Poisson)

Antes de cada partido T, usando SOLO partidos con date < T (nada de futuro).

Para cada equipo:

- `att` ataque (capacidad de hacer goles)
- `def` defensa (capacidad de recibir goles; más alto = peor defensa, o usar signo y documentarlo)
- `home_adv` ventaja de local (un parámetro de liga, no de equipo, al inicio)
- `form_gf_5`, `form_ga_5` goles a favor/en contra últimos 5
- `games_played`
- `rest_days` si hay calendario
- `elo` opcional

Estimación clásica de att/def (elige una y documentala en código):

**Opción A — medias suavizadas (más simple, buena para MVP)**

Para una liga y una ventana (ej. últimos 8–12 meses, decaimiento exponencial por fecha):

```
league_avg_home_goals = media de home_goals
league_avg_away_goals = media de away_goals

att_home = (goles hechos como local / partidos local) / league_avg_home_goals
def_home = (goles recibidos como local / partidos local) / league_avg_away_goals

att_away = (goles hechos como visita / partidos visita) / league_avg_away_goals
def_away = (goles recibidos como visita / partidos visita) / league_avg_home_goals
```

Suavizar equipos con pocos partidos hacia 1.0 (regresión a la media):

```
att = (n * att_raw + k * 1.0) / (n + k)    # k = 6 por ejemplo
```

Decaimiento temporal: partidos más viejos pesan menos.

```
weight = 0.5 ** (days_ago / 180)     # semivida ~6 meses, ajustable
```

**Opción B — Dixon-Coles / máxima verosimilitud**  
Ajustar att_i, def_i, home_adv sobre el log-likelihood de los goles. Mejor, más código. Dejarla como `model_type: "dixon_coles"` en config.

MVP implementa Opción A. Dejar interfaz para B.

### 11.4 Goles esperados del partido

```
λ_home = league_avg_home_goals * att_home * def_away * home_adv
λ_away = league_avg_away_goals * att_away * def_home
```

`home_adv` inicial ≈ 1.10 a 1.35 según liga (calibrar en backtest; 1.25 es un arranque razonable).

Clamp de seguridad:

```
λ_home, λ_away ∈ [0.20, 4.00]
```

### 11.5 Matriz de marcadores

Sea X ~ Poisson(λ_home), Y ~ Poisson(λ_away), independientes en el MVP.

Para g, h = 0..MAX_GOALS (MAX_GOALS = 8):

```
P(X=g, Y=h) = e^{-λh} λh^g / g!  *  e^{-λa} λa^h / h!
```

Renormalizar para que la suma del grid 0..8 sea 1 (la cola 9+ se reparte o se ignora; documentar).  
Tests: suma total ∈ [0.99, 1.01] antes de renormalizar; después = 1.000.

Dixon-Coles (fase 1.5): multiplicar P(0-0), P(1-0), P(0-1), P(1-1) por factor ρ. Implementar si hay tiempo.

### 11.6 Cómo sale cada mercado (de la misma matriz)

**1X2**

```
P_H = sum P(g,h) donde g > h
P_D = sum P(g,h) donde g = h
P_A = sum P(g,h) donde g < h
```

**BTTS**

```
P_yes = sum P(g,h) donde g ≥ 1 y h ≥ 1
P_no  = 1 - P_yes
```

**Over/Under línea L** (L = 1.5, 2.5, 3.5)

```
P_over  = sum P(g,h) donde (g+h) > L
P_under = sum P(g,h) donde (g+h) < L
```

Para líneas .5 no hay push.

**Resultado exacto**

Ordenar P(g,h) descendente. Devolver top 3 o top 5.

**Team OU** (fase 2)

```
P(home over 1.5) = sum P(g,h) donde g ≥ 2
```

### 11.7 JSON que el bot / LLM recibe

```json
{
  "fixture_id": "epl_2026-08-30_mci_ars",
  "kickoff": "2026-08-30T15:00:00-03:00",
  "competition_id": "EPL",
  "home": "Manchester City",
  "away": "Arsenal",
  "lambda_home": 1.72,
  "lambda_away": 1.18,
  "markets": {
    "1x2": {"H": 0.48, "D": 0.26, "A": 0.26},
    "btts": {"yes": 0.58, "no": 0.42},
    "ou": {
      "1.5": {"over": 0.78, "under": 0.22},
      "2.5": {"over": 0.55, "under": 0.45},
      "3.5": {"over": 0.33, "under": 0.67}
    },
    "cs_top": [
      {"score": "1-1", "p": 0.12},
      {"score": "2-1", "p": 0.10},
      {"score": "1-0", "p": 0.09}
    ]
  },
  "factors": [
    "City tiene mejor ataque suavizado que Arsenal en la ventana",
    "Arsenal concede menos de la media de liga como visita",
    "Ventaja de local aplicada: 1.25"
  ],
  "confidence": "media",
  "model": "poisson_v1",
  "trained_until": "2026-08-27"
}
```

`factors` los arma el motor con reglas (comparar att/def vs media). El LLM no inventa factores.

### 11.8 Ejemplo numérico trabajado (partido ilustrativo)

Partido ficticio de calibración: **River Plate vs Boca Juniors** (no usar como fixture real si no existe esa fecha).

Supuestos de liga (inventados para el ejemplo, el código debe calcularlos de data real):

```
league_avg_home_goals = 1.40
league_avg_away_goals = 1.10
home_adv = 1.25

att_river = 1.20
def_river = 0.90
att_boca  = 1.10
def_boca  = 1.00
```

λ:

```
λ_home = 1.40 * 1.20 * 1.00 * 1.25 = 2.10
λ_away = 1.10 * 1.10 * 0.90       = 1.089  → 1.09
```

Interpretación: River ~2.10 goles esperados, Boca ~1.09.

Con Poisson independiente (aprox., no hace falta que el implementador reproduzca cada decimal a mano; sí debe escribir tests con estos λ):

Orden de magnitud esperado:

- 1X2: local claro favorito (P_H ~ 55–60%, P_D ~ 22–25%, P_A ~ 18–22%)
- BTTS sí ~ 55–60%
- Over 2.5 ~ 55–60% (λ total ≈ 3.19)
- Exactos altos: 2-1, 1-1, 2-0, 3-1

El test `test_example_river_boca` puede fijar estos λ y asertar:

- P_H > P_A
- P_H + P_D + P_A ≈ 1
- P_over_2.5 > 0.50
- top scoreline está en {(2,1),(1,1),(2,0),(3,1),(1,0)}

### 11.9 Entrenamiento / “nutrir”

Job `train_or_refresh`:

1. Ingerir resultados nuevos.
2. Recalcular ratings con corte temporal.
3. Guardar `ratings.parquet` + metadata (`as_of` date).
4. Para cada fixture futuro a 7–14 días: `predict()` y guardar snapshot en `data/predictions/YYYY-MM-DD.json`.
5. Después del partido: `settle()` compara predicción vs resultado.

Nunca reentrenar usando el resultado del partido que estás prediciendo.

Frecuencia MVP: 1 vez al día + on-demand antes de una consulta si el snapshot es viejo (>12 h).

### 11.10 Evaluación (obligatorio, aunque sea simple)

Métricas:

- Accuracy 1X2 (el lado de mayor P)
- Log-loss 1X2
- Brier score 1X2
- Accuracy BTTS (umbral 0.5)
- Accuracy O/U 2.5 (umbral 0.5)
- Calibration: en bins de 10%, ¿pasó lo que decía el %?

Baseline a vencer:

- “siempre local”
- “siempre favorito de cuota” si hay odds
- media de liga

Si el modelo no le gana a “siempre local” en una liga, no abrir esa liga al público.

Hit-rate público (`/historial`) = settlement de snapshots **pre-partido**, no recálculo a posteriori.

---

## 12. Capa conversacional (cómo usar el LLM)

Dos modos. Implementar los dos si se puede; el modo A funciona sin API key.

### Modo A — plantillas (default, barato, predecible)

`render.py` llena la plantilla 9.7.  
One-liners desde una lista según rangos de probabilidad.

### Modo B — LLM narrator

Prompt de sistema fijo (guardar en `src/nlp/system_prompt.txt`):

```
Sos Botinho777, asistente de análisis de fútbol.
Hablás en español, de vos, amable, educado, con una sola línea de humor liviano.
NUNCA inventes números. Usá SOLO el JSON que te pasan.
NUNCA digas "apuesta", "está cantado", "te aseguro", "ganancia segura".
Si el JSON no trae un mercado, decí que no lo calculaste.
Cerrá con: "Análisis del modelo. No es una garantía."
Máximo 220 palabras salvo que pidan más detalle.
```

User prompt = JSON + pregunta original del usuario.

Proveedor: configurable por env (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.). El dueño lo va a correr con Claude Code; no hardcodear un vendor.

---

## 13. Criterios de aceptación del MVP

Listo para “sí, esto es Botinho777” cuando:

1. `/start` muestra copy + menú.
2. Hay al menos 1 liga con fixtures reales o de un CSV de prueba.
3. Un partido devuelve JSON de motor + mensaje en tono Botinho.
4. 1X2 + BTTS + O/U 2.5 + top 3 exactos salen del mismo λ.
5. Las tres probs 1X2 suman 1 ± 0.01.
6. Tope free funciona.
7. Disclaimer aparece.
8. Tests del Poisson pasan.
9. README explica: cómo cargar un CSV, correr `predict`, correr el bot en polling.

Fuera de MVP (no bloquear):

- Pagos automáticos
- Paraguay / League One en producción
- Dixon-Coles
- App web
- Fine-tune de LLM

---

## 14. Variables de entorno

```
TELEGRAM_BOT_TOKEN=
ADMIN_TELEGRAM_ID=
LLM_PROVIDER=none|openai|anthropic
LLM_API_KEY=
LLM_MODEL=
DATABASE_PATH=data/botinho.db
MAX_FREE_QUERIES_PER_DAY=5
TIMEZONE=America/Asuncion
```

---

## 15. Principios para Claude Code

1. El motor es la fuente de verdad. El texto es maquillaje.
2. Sin dato → no hay número. Mensaje honesto.
3. Código testeable en `markets.py` y `poisson.py` primero; el bot después.
4. Commits chicos: ingest → ratings → markets → renderer → bot.
5. No descargar datasets enormes sin que el usuario lo pida; incluir un CSV de ejemplo de 200–500 partidos sintéticos o reales de una liga para que el repo corra offline.
6. Comentarios en español o inglés, da igual; nombres de funciones en inglés.
7. No incluir secretos.

---

## 16. Primeras tareas de implementación (orden)

1. Repo + CSV de ejemplo + schema pydantic del JSON de predicción.
2. `poisson.py` + `markets.py` + tests con el ejemplo River-Boca (λ fijos).
3. `features.py` + ratings desde CSV histórico.
4. `predict.py` CLI: `python -m src.model.predict --home "A" --away "B"`
5. `render.py` plantilla sin LLM.
6. Bot Telegram: /start, elegir partido demo, responder paquete.
7. Contador free + rol premium manual (admin command `/grant <user_id> 30`).
8. Snapshot + settle + /historial dummy.

Cuando esto corre en local, el producto ya se puede mostrar.

---

Fin del spec.
