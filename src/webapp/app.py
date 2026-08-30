"""Demo web con Streamlit: login + tope free/premium + paquete.

No toca el motor: solo usa build_prediction (src/model/predict.py) y
render_paquete (src/nlp/render.py) tal cual estan. Correr con:
    python -m streamlit run src/webapp/app.py
"""
from __future__ import annotations

import os
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.bot.copy import CHAT_TOPE_FREE_TEXT, PLANES_TEXT, TOPE_FREE_TEXT
from src.data.features import load_matches
from src.eval.historial import NO_HISTORIAL_TEXT
from src.eval.settle import DEFAULT_RESULTS_CSV
from src.eval.snapshot import build_snapshot
from src.model.predict import DEFAULT_COMPETITION, DEFAULT_CSV, build_prediction
from src.nlp.chat import LlmNotConfiguredError, ask_llm
from src.nlp.render import DISCLAIMER_SHORT, render_paquete
from src.webapp.auth import (
    EmailAlreadyRegisteredError,
    InvalidResetCodeError,
    authenticate,
    get_user,
    register_user,
    request_password_reset,
    reset_password,
)
from src.webapp.email import EmailNotConfiguredError

REAL_CSV = "data/raw/real_matches.csv"
UPCOMING_CSV = "data/raw/upcoming_fixtures.csv"
LEAGUE_NAMES = {
    "CHAMPIONS": "Champions League",
    "LALIGA": "La Liga",
    "PREMIER": "Premier League",
    "SERIEA": "Serie A",
}
PY_TZ = ZoneInfo("America/Asuncion")
from src.webapp.quota import can_ask_chat_question, can_query, is_premium_active, register_chat_question, register_query

st.set_page_config(page_title="Botinho777", page_icon="⚽", layout="wide")

_LANDING_CSS = """
<style>
@keyframes bt-fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Layout wide da todo el ancho de la ventana; lo recentramos con un
   maximo razonable para que la navbar tenga lugar sin apretarse (antes
   el layout "centered" default de Streamlit dejaba ~730px, muy poco
   para logo + 4 links + 2 botones en una sola fila). */
.block-container {
  max-width: 1180px;
  padding-top: 2rem;
  padding-left: 2rem;
  padding-right: 2rem;
}

.bt-hero-wrap { position: relative; padding: 1.75rem 0 .5rem 0; }
.bt-hero-wrap::before {
  content: "";
  position: absolute;
  /* Antes empezaba en top:-60px y se metia por detras del header,
     mezclandose con el verde del boton "Registrarme". Arranca mas abajo
     (dentro del propio hero) para no pisar la navbar. */
  top: 20px; left: 50%;
  transform: translateX(-50%);
  width: 820px; height: 280px;
  background: radial-gradient(ellipse at center, rgba(34,197,94,0.20) 0%, rgba(34,197,94,0.05) 45%, transparent 72%);
  pointer-events: none;
  z-index: 0;
}
.bt-hero-title {
  position: relative; z-index: 1;
  font-size: 2.5rem; font-weight: 750; line-height: 1.15; margin: 0 0 .55rem 0;
  background: linear-gradient(180deg, #ffffff 0%, #b9c9c0 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: bt-fade-up .55s ease-out both;
}
.bt-hero-title .bt-accent {
  background: linear-gradient(90deg, #22c55e, #4ade80);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.bt-hero-sub {
  position: relative; z-index: 1; color: #9fb3a8; font-size: 1.02rem; max-width: 640px;
  animation: bt-fade-up .55s ease-out .08s both;
}

.bt-card {
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.025);
  border-radius: 14px; padding: 1.1rem 1.3rem;
  animation: bt-fade-up .55s ease-out .1s both;
}
.bt-badge {
  display: inline-block; background: rgba(34,197,94,0.15); color: #4ade80;
  border: 1px solid rgba(34,197,94,0.3); font-size: .7rem; font-weight: 700;
  letter-spacing: .04em; padding: .15rem .55rem; border-radius: 999px; text-transform: uppercase;
}
.bt-lock-line { color: #8ba396; font-size: .85rem; margin-top: .55rem; display: flex; align-items: center; gap: .4rem; }

.bt-steps { display: flex; gap: 1rem; margin-top: .9rem; flex-wrap: wrap; }
.bt-step {
  flex: 1 1 220px; border: 1px solid rgba(255,255,255,0.07); background: rgba(255,255,255,0.015);
  border-radius: 12px; padding: 1.05rem 1.15rem; animation: bt-fade-up .55s ease-out both;
}
.bt-step:nth-child(1) { animation-delay: .05s; }
.bt-step:nth-child(2) { animation-delay: .15s; }
.bt-step:nth-child(3) { animation-delay: .25s; }
.bt-step-num {
  display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px;
  border-radius: 50%; background: #22c55e; color: #06210f; font-weight: 700; font-size: .78rem;
}
.bt-step-icon { font-size: 1.15rem; margin-left: .45rem; }
.bt-step-title { font-weight: 650; color: #e7f3ec; margin: .45rem 0 .2rem 0; font-size: .95rem; }
.bt-step-text { color: #94a89d; font-size: .85rem; line-height: 1.4; }

.bt-quote {
  border-left: 3px solid #22c55e; background: rgba(34,197,94,0.05);
  padding: .85rem 1.05rem; border-radius: 0 10px 10px 0; color: #d9ece2; font-size: .96rem;
  margin: 1.3rem 0;
}

.bt-footer-rule { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 1.5rem 0 .7rem 0; }

.bt-logo {
  display: flex; align-items: center; gap: .55rem;
  font-size: 1.25rem; font-weight: 700; color: #e7f3ec; white-space: nowrap;
}
.bt-logo-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px; border-radius: 9px; background: #22c55e;
  font-size: 1.1rem; flex-shrink: 0;
}

/* La fila del header (logo / nav / botones) viene de st.columns, que por
   default pone align-items:stretch en div[data-testid="stHorizontalBlock"]
   (confirmado inspeccionando el DOM real). vertical_alignment="center" de
   Streamlit NO cambia ese align-items: en cambio calcula un margin-top a
   mano por columna via JS, que no da el mismo centro visual que el link de
   adentro (por eso el fix anterior con un margin-top a ojo era fragil).
   En vez de forzar align-items:center en TODOS los stHorizontalBlock de la
   pagina (rompe el alto parejo de las tarjetas de Planes/Cómo funciona,
   que dependen de stretch — verificado en vivo: sin stretch la tarjeta
   "Gratis" se encoge de 254px a 102px), marcamos solo la fila del header
   con un span invisible y usamos :has() para scopear el override.
   El span vive dentro del HTML del logo (unico div.stHorizontalBlock que
   lo contiene). */
.bt-header-row-marker { display: none; }
div[data-testid="stHorizontalBlock"]:has(.bt-header-row-marker) {
  align-items: center !important;
}
/* Causa raiz real (confirmada en vivo con getComputedStyle):
   div[data-testid="stMarkdownContainer"] trae de fabrica un
   margin-bottom: -16px (Streamlit lo usa para compactar el espacio entre
   bloques de texto apilados). align-items:center centra la CAJA DE MARGEN
   del flex-item, no la caja visible: con ese margen negativo la caja de
   margen mide ~7.5px aunque el texto visible mida ~23.5px, así que el
   logo y los links quedaban centrados mal (~8px mas abajo que los
   botones). Neutralizar ese margen dentro de la fila del header alcanza
   solo con eso (probado en vivo: con margin-bottom:0 el centro del link
   "Planes" cae exactamente en el mismo pixel que el centro del boton
   "Registrarme", sin necesidad de forzar ningun alto fijo). */
div[data-testid="stHorizontalBlock"]:has(.bt-header-row-marker)
  div[data-testid="stMarkdownContainer"] {
  margin-bottom: 0 !important;
}

.bt-nav-links {
  display: flex; align-items: center; justify-content: center; gap: 1.4rem; flex-wrap: nowrap;
}
.bt-nav-links a {
  color: #b7c7bd; font-size: .92rem; font-weight: 500; text-decoration: none; white-space: nowrap;
}
.bt-nav-links a:hover { color: #4ade80; }

.bt-section-title {
  font-size: 1.4rem; font-weight: 700; color: #e7f3ec; margin: 2.2rem 0 .9rem 0;
}

.bt-plan-card { position: relative; overflow: hidden; }
.bt-plan-card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: rgba(255,255,255,0.12);
}
.bt-plan-card.bt-plan-premium::before { background: linear-gradient(90deg, #22c55e, #4ade80); }
.bt-plan-name { font-weight: 700; font-size: 1.05rem; color: #e7f3ec; margin-bottom: .4rem; }
.bt-plan-price { font-size: 1.4rem; font-weight: 700; color: #4ade80; margin: .3rem 0 .6rem 0; }
.bt-plan-body { color: #a8bcb1; font-size: .88rem; line-height: 1.7; white-space: pre-line; }

.bt-historial-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: .9rem; }
.bt-historial-stat {
  flex: 1 1 150px; border: 1px solid rgba(255,255,255,0.07); background: rgba(255,255,255,0.015);
  border-radius: 12px; padding: 1rem 1.1rem; text-align: center;
}
.bt-historial-number { font-size: 1.7rem; font-weight: 750; color: #4ade80; }
.bt-historial-label { color: #94a89d; font-size: .78rem; margin-top: .3rem; }

div.stButton > button {
  transition: transform .18s ease, box-shadow .18s ease;
  padding: .55rem 1.1rem;
  border-radius: 10px;
  white-space: nowrap;
}
div.stButton > button:hover {
  transform: scale(1.04);
  box-shadow: 0 0 0 1px rgba(34,197,94,.35), 0 6px 18px rgba(34,197,94,.15);
}
div.stButton > button:focus-visible {
  outline: 2px solid #22c55e !important; outline-offset: 2px;
}

@media (max-width: 640px) {
  .bt-hero-title { font-size: 1.85rem; }
  .bt-steps { flex-direction: column; }
}
@media (max-width: 768px) {
  .bt-nav-links { display: none; }
}
</style>
"""


@st.cache_data
def _team_ids(csv_path: str, competition_id: str) -> list[str]:
    df = load_matches(csv_path)
    teams = set(df[df["competition_id"] == competition_id]["home_team_id"]) | set(
        df[df["competition_id"] == competition_id]["away_team_id"]
    )
    return sorted(teams)


@st.cache_data
def _available_competitions(csv_path: str) -> list[str]:
    df = load_matches(csv_path)
    return sorted(df["competition_id"].unique())


def _pick_data_source() -> tuple[str, list[str]]:
    """Devuelve (csv_path, competition_ids) usando datos reales si ya se
    cargaron con scripts/fetch_real_data.py, o la liga demo si no."""
    if os.path.exists(REAL_CSV):
        real_competitions = _available_competitions(REAL_CSV)
        if real_competitions:
            return REAL_CSV, real_competitions
    return DEFAULT_CSV, [DEFAULT_COMPETITION]


@st.cache_data(ttl=300)
def _load_upcoming_fixtures() -> pd.DataFrame:
    """Calendario real bajado con scripts/fetch_fixtures.py (hoy en adelante).
    Vacio si todavia no se corrio ese script."""
    if not os.path.exists(UPCOMING_CSV):
        return pd.DataFrame()
    df = pd.read_csv(UPCOMING_CSV)
    df["kickoff_utc"] = pd.to_datetime(df["kickoff_utc"], utc=True)
    now = pd.Timestamp.now(tz="UTC")
    return df[df["kickoff_utc"] >= now].sort_values("kickoff_utc").reset_index(drop=True)


def _fixture_label(row: pd.Series) -> str:
    local = row["kickoff_utc"].tz_convert(PY_TZ)
    return f"{local.strftime('%d/%m %H:%M')} · {row['home_team_name']} vs {row['away_team_name']}"


_NAME_ACRONYMS = {"fc", "cf", "ac", "sc", "cd", "ca", "as", "us", "kv", "afc"}


def _prettify_team_id(team_id: str) -> str:
    """Fallback si no hay nombre real cacheado (ej. equipos de la liga demo):
    arma un titulo legible a partir del id (fc_barcelona -> FC Barcelona)."""
    words = team_id.replace("-", "_").split("_")
    return " ".join(w.upper() if w in _NAME_ACRONYMS else w.capitalize() for w in words)


@st.cache_data(ttl=300)
def _team_name_map() -> dict[str, str]:
    """id de equipo (usado internamente por el motor) -> nombre real, juntando
    lo que haya en el historial y en el calendario de proximos partidos."""
    name_map: dict[str, str] = {}
    for path in (REAL_CSV, UPCOMING_CSV):
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        if "home_team_name" not in df.columns:
            continue
        for _, row in df[["home_team_id", "home_team_name"]].drop_duplicates().iterrows():
            name_map[row["home_team_id"]] = row["home_team_name"]
        for _, row in df[["away_team_id", "away_team_name"]].drop_duplicates().iterrows():
            name_map[row["away_team_id"]] = row["away_team_name"]
    return name_map


def _display_name(team_id: str, name_map: dict[str, str]) -> str:
    return name_map.get(team_id, _prettify_team_id(team_id))


def _prettify_prediction(prediction: dict) -> dict:
    """Reemplaza los team_id crudos del JSON del motor por nombres reales para
    mostrar en pantalla/mandar al chat. Solo texto de presentacion: no toca
    lambdas, probabilidades ni ningun calculo."""
    name_map = _team_name_map()
    home_id, away_id = prediction["home"], prediction["away"]
    home_name = _display_name(home_id, name_map)
    away_name = _display_name(away_id, name_map)
    prediction = dict(prediction)
    prediction["home"] = home_name
    prediction["away"] = away_name
    prediction["factors"] = [
        f.replace(home_id, home_name).replace(away_id, away_name) for f in prediction["factors"]
    ]
    return prediction


def _reset_password_popover() -> None:
    """Botón chico al lado de la contraseña: pedís el email y te llega un link
    (no un código) que abre una página aparte para poner la contraseña nueva."""
    with st.popover("¿Olvidaste tu contraseña?", type="tertiary", use_container_width=False):
        if st.session_state.get("reset_link_sent"):
            st.success("Si ese email está registrado, te mandamos un link para restablecer tu contraseña.")
            return

        email = st.text_input("Email", key="reset_email")
        if st.button("Enviar link", key="reset_send_link_btn"):
            try:
                request_password_reset(email.strip().lower())
            except EmailNotConfiguredError:
                st.error(
                    "Todavía no configuré el envío de emails (falta SMTP_USER/SMTP_APP_PASSWORD "
                    "en el .env)."
                )
            else:
                st.session_state["reset_link_sent"] = True


def _reset_password_page(email: str, token: str) -> None:
    st.title("⚽ Botinho777")
    st.subheader("Restablecer contraseña")

    new_password = st.text_input("Contraseña nueva", type="password", key="reset_page_new_password")
    confirm_password = st.text_input(
        "Confirmá la contraseña nueva", type="password", key="reset_page_confirm_password"
    )

    if st.button("Cambiar contraseña", type="primary"):
        if len(new_password) < 6:
            st.error("La contraseña tiene que tener al menos 6 caracteres.")
        elif new_password != confirm_password:
            st.error("Las dos contraseñas no coinciden.")
        else:
            try:
                reset_password(email, token, new_password)
            except InvalidResetCodeError:
                st.error("Este link es inválido o ya venció. Pedí uno nuevo desde el login.")
            else:
                st.session_state["reset_page_done"] = True

    if st.session_state.get("reset_page_done"):
        st.success("Contraseña actualizada. Ya podés cerrar esta pestaña e iniciar sesión con la nueva.")
        if st.button("Ir al login"):
            st.query_params.clear()
            st.rerun()


@st.dialog("Iniciar sesión")
def _login_dialog() -> None:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Contraseña", type="password", key="login_password")
    _reset_password_popover()

    if st.button("Iniciar sesión", type="primary"):
        user = authenticate(email.strip().lower(), password)
        if user is None:
            st.error("Email o contraseña incorrectos.")
        else:
            st.session_state["user_email"] = user["email"]
            st.rerun()


@st.dialog("Registrarme")
def _register_dialog() -> None:
    email = st.text_input("Email", key="registro_email")
    password = st.text_input("Contraseña", type="password", key="registro_password")

    if st.button("Registrarme", type="primary"):
        email_norm = email.strip().lower()
        if not email_norm or "@" not in email_norm:
            st.error("Poné un email válido.")
        elif len(password) < 6:
            st.error("La contraseña tiene que tener al menos 6 caracteres.")
        else:
            try:
                register_user(email_norm, password)
            except EmailAlreadyRegisteredError as exc:
                st.error(str(exc))
            else:
                st.session_state["user_email"] = email_norm
                st.rerun()


def _landing_page() -> None:
    st.markdown(_LANDING_CSS, unsafe_allow_html=True)

    col_logo, col_nav, col_actions = st.columns([2.2, 4, 2.8])
    col_logo.markdown(
        '<span class="bt-header-row-marker"></span>'
        '<div class="bt-logo"><span class="bt-logo-badge">⚽</span>Botinho777</div>',
        unsafe_allow_html=True,
    )
    col_nav.markdown(
        """
        <div class="bt-nav-links">
          <a href="#como-funciona">Cómo funciona</a>
          <a href="#planes">Planes</a>
          <a href="#historial">Historial</a>
          <a href="#faq">Preguntas frecuentes</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_login, col_registro = col_actions.columns(2)
    if col_login.button("Iniciar sesión", use_container_width=True):
        _login_dialog()
    if col_registro.button("Registrarme", type="primary", use_container_width=True):
        _register_dialog()

    st.markdown(
        """
        <div class="bt-hero-wrap">
          <div class="bt-hero-title">Fútbol leído con <span class="bt-accent">números</span>,<br>no con humo</div>
          <div class="bt-hero-sub">
            1X2, ambos marcan, más/menos goles y el marcador más probable — calculado por un
            modelo estadístico, sin inventar ni prometer resultados.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    teaser_csv, teaser_competitions = _pick_data_source()
    teaser_fixtures = _load_upcoming_fixtures()
    if teaser_csv != DEFAULT_CSV and not teaser_fixtures.empty:
        teaser_row = teaser_fixtures.iloc[0]
        teaser_matchup = f"{teaser_row['home_team_name']} vs {teaser_row['away_team_name']}"
        teaser_label = LEAGUE_NAMES.get(teaser_row["competition_id"], teaser_row["competition_id"])
        teaser_when = teaser_row["kickoff_utc"].tz_convert(PY_TZ).strftime("%d/%m %H:%M")
        teaser_badge = "En vivo"
        teaser_sub = f"{teaser_matchup} · {teaser_label} · {teaser_when} (PY)"
    else:
        teaser_competition = teaser_competitions[0]
        teaser_teams = _team_ids(teaser_csv, teaser_competition)
        teaser_label = LEAGUE_NAMES.get(teaser_competition, teaser_competition)
        teaser_badge = "Demo" if teaser_csv == DEFAULT_CSV else "En vivo"
        teaser_sub = f"{teaser_teams[0]} vs {teaser_teams[1]} · {teaser_label}"
    st.markdown(
        f"""
        <div class="bt-card">
          <span class="bt-badge">{teaser_badge}</span>
          <div style="margin-top:.6rem; font-size:1.05rem; font-weight:600; color:#e7f3ec;">
            {teaser_sub}
          </div>
          <div class="bt-lock-line">🔒 Iniciá sesión (es gratis) para ver el paquete completo de este cruce y preguntarle al chat.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div id="como-funciona"></div>', unsafe_allow_html=True)
    st.markdown("#### Cómo funciona")
    st.markdown(
        """
        <div class="bt-steps">
          <div class="bt-step">
            <span class="bt-step-num">1</span><span class="bt-step-icon">📊</span>
            <div class="bt-step-title">Historial y forma</div>
            <div class="bt-step-text">Goles a favor/en contra y localía de cada equipo.</div>
          </div>
          <div class="bt-step">
            <span class="bt-step-num">2</span><span class="bt-step-icon">🧮</span>
            <div class="bt-step-title">El motor calcula</div>
            <div class="bt-step-text">Probabilidades por un modelo estadístico, no por un LLM.</div>
          </div>
          <div class="bt-step">
            <span class="bt-step-num">3</span><span class="bt-step-icon">💬</span>
            <div class="bt-step-title">Te lo cuento en cristiano</div>
            <div class="bt-step-text">El paquete y el chat, ambos leyendo el mismo cálculo.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="bt-quote">Si el partido está 50/50, te lo digo. No vendo certeza falsa.</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div id="planes"></div>', unsafe_allow_html=True)
    st.markdown('<div class="bt-section-title">Planes</div>', unsafe_allow_html=True)

    plan_parts = PLANES_TEXT.split("\n\n")
    gratis_lines = plan_parts[0].split("\n")
    premium_lines = plan_parts[1].split("\n") + [""] + plan_parts[2].split("\n")

    col_gratis, col_premium = st.columns(2)
    col_gratis.markdown(
        f"""
        <div class="bt-card bt-plan-card">
          <div class="bt-plan-name">{gratis_lines[0]}</div>
          <div class="bt-plan-body">{chr(10).join(gratis_lines[1:])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_premium.markdown(
        f"""
        <div class="bt-card bt-plan-card bt-plan-premium">
          <div class="bt-plan-name">{premium_lines[0]}</div>
          <div class="bt-plan-body">{chr(10).join(premium_lines[1:])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div id="historial"></div>', unsafe_allow_html=True)
    st.markdown('<div class="bt-section-title">Historial</div>', unsafe_allow_html=True)

    hist_df = pd.read_csv(DEFAULT_RESULTS_CSV) if os.path.exists(DEFAULT_RESULTS_CSV) else pd.DataFrame()
    if hist_df.empty:
        st.markdown(f'<div class="bt-card">{NO_HISTORIAL_TEXT}</div>', unsafe_allow_html=True)
    else:
        n = len(hist_df)
        acc_1x2 = hist_df["hit_1x2"].mean()
        acc_btts = hist_df["hit_btts"].mean()
        acc_ou25 = hist_df["hit_ou_2.5"].mean()
        acc_exact_top3 = hist_df["hit_exact_top3"].mean()
        st.markdown(
            f"""
            <div class="bt-historial-grid">
              <div class="bt-historial-stat"><div class="bt-historial-number">{acc_1x2:.0%}</div><div class="bt-historial-label">Acierto 1X2</div></div>
              <div class="bt-historial-stat"><div class="bt-historial-number">{acc_btts:.0%}</div><div class="bt-historial-label">Ambos marcan</div></div>
              <div class="bt-historial-stat"><div class="bt-historial-number">{acc_ou25:.0%}</div><div class="bt-historial-label">Over/under 2.5</div></div>
              <div class="bt-historial-stat"><div class="bt-historial-number">{acc_exact_top3:.0%}</div><div class="bt-historial-label">Top 3 marcador</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Sobre {n} partidos. Backtest ilustrativo de la liga demo — no es un historial de ligas reales.")

    st.markdown('<div id="faq"></div>', unsafe_allow_html=True)
    st.markdown('<div class="bt-section-title">Preguntas frecuentes</div>', unsafe_allow_html=True)
    with st.expander("¿Es una casa de apuestas?"):
        st.write(DISCLAIMER_SHORT)
    with st.expander("¿Qué pasa si me quedo sin consultas gratis?"):
        st.write(TOPE_FREE_TEXT)

    st.markdown('<hr class="bt-footer-rule">', unsafe_allow_html=True)
    st.caption(DISCLAIMER_SHORT)


def _status_caption(user: dict) -> str:
    if is_premium_active(user):
        return f"Cuenta: {user['email']} · Premium hasta {user['premium_until']}"
    return f"Cuenta: {user['email']} · Free · {user['daily_count']} consultas usadas hoy"


def _paquete_form(user: dict) -> None:
    st.title("Botinho777")
    col_status, col_logout = st.columns([4, 1])
    col_status.caption(_status_caption(user))
    if col_logout.button("Salir"):
        del st.session_state["user_email"]
        st.rerun()

    csv_path, competitions = _pick_data_source()
    fixture_kickoff = None
    if csv_path == DEFAULT_CSV:
        st.caption(
            f"Liga de demostración: {DEFAULT_COMPETITION} (equipos del CSV de ejemplo). "
            "Todavía no se cargaron datos reales — correr `python -m scripts.fetch_real_data` "
            "con `FOOTBALL_DATA_API_KEY` configurada en `.env`."
        )
        competition = DEFAULT_COMPETITION
        teams = _team_ids(csv_path, competition)
        col_home, col_away = st.columns(2)
        home = col_home.selectbox("Local", teams, index=0)
        away_options = [t for t in teams if t != home]
        away = col_away.selectbox("Visita", away_options, index=0)
    else:
        competition = st.selectbox(
            "Competición",
            competitions,
            format_func=lambda c: LEAGUE_NAMES.get(c, c),
        )
        all_fixtures = _load_upcoming_fixtures()
        fixtures = (
            all_fixtures[all_fixtures["competition_id"] == competition]
            if not all_fixtures.empty
            else all_fixtures
        )
        if fixtures.empty:
            st.info(
                "Todavía no hay calendario de próximos partidos cargado para esta "
                "competición — correr `python -m scripts.fetch_fixtures`. Mientras "
                "tanto, elegí un cruce a mano con el historial:"
            )
            teams = _team_ids(csv_path, competition)
            col_home, col_away = st.columns(2)
            home = col_home.selectbox("Local", teams, index=0)
            away_options = [t for t in teams if t != home]
            away = col_away.selectbox("Visita", away_options, index=0)
        else:
            chosen_idx = st.selectbox(
                "Partido (hoy, próximos días, semana y mes)",
                fixtures.index,
                format_func=lambda i: _fixture_label(fixtures.loc[i]),
            )
            chosen = fixtures.loc[chosen_idx]
            home, away = chosen["home_team_id"], chosen["away_team_id"]
            fixture_kickoff = chosen["kickoff_utc"]

    if st.button("Paquete"):
        if not can_query(user):
            st.warning(TOPE_FREE_TEXT)
            with st.expander("Planes"):
                st.text(PLANES_TEXT)
        else:
            if fixture_kickoff is not None:
                hist_df = load_matches(csv_path)
                as_of = fixture_kickoff.tz_localize(None)
                try:
                    prediction = build_snapshot(
                        hist_df, competition, home, away, as_of=as_of, kickoff_iso=fixture_kickoff.isoformat()
                    )
                except ValueError:
                    prediction = build_prediction(csv_path, competition, home, away)
            else:
                prediction = build_prediction(csv_path, competition, home, away)
            st.session_state["last_prediction"] = _prettify_prediction(prediction)
            st.session_state["chat_history"] = []
            register_query(user)

    prediction = st.session_state.get("last_prediction")
    if prediction is not None:
        text = render_paquete(prediction)
        # render_paquete usa saltos de linea simples (pensado para Telegram);
        # en markdown de Streamlit un \n solo no corta linea, asi que agregamos
        # el salto de linea "duro" de markdown (dos espacios) sin tocar render.py.
        with st.container(border=True):
            st.markdown(text.replace("\n", "  \n"))
        _chat_section(user, prediction)

    st.divider()
    st.caption(DISCLAIMER_SHORT)


def _chat_section(user: dict, prediction: dict) -> None:
    st.subheader("Preguntale a Botinho777")
    st.caption("Solo responde sobre el partido que acabás de consultar. No inventa números fuera del JSON del motor.")

    with st.container(border=True):
        history = st.session_state.setdefault("chat_history", [])
        for turn in history:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])

        question = st.chat_input("Preguntá algo sobre este partido...")
        if not question:
            return

        if not is_premium_active(user) and not can_ask_chat_question(user):
            with st.chat_message("assistant"):
                st.warning(CHAT_TOPE_FREE_TEXT)
            return

        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        answered = True
        with st.chat_message("assistant"):
            try:
                answer = ask_llm(prediction, question, history=history[:-1])
            except LlmNotConfiguredError:
                answered = False
                answer = (
                    "Todavía no tengo el LLM conectado (falta LLM_API_KEY en el .env), "
                    "así que no puedo charlar libremente todavía. Probá pedir el Paquete de nuevo mientras tanto."
                )
            st.markdown(answer)

        history.append({"role": "assistant", "content": answer})
        if answered and not is_premium_active(user):
            register_chat_question(user)


def main() -> None:
    reset_email = st.query_params.get("reset_email")
    reset_token = st.query_params.get("reset_token")
    if reset_email and reset_token:
        _reset_password_page(reset_email, reset_token)
        return

    email = st.session_state.get("user_email")
    user = get_user(email) if email else None

    if user is None:
        st.session_state.pop("user_email", None)
        _landing_page()
    else:
        _paquete_form(user)


if __name__ == "__main__":
    main()
