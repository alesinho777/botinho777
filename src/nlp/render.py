"""Renderer sin LLM: JSON del motor -> texto Botinho777 (seccion 9.7 y Modo A de la 12).

Regla de oro: esto no calcula nada, solo narra el JSON que ya vino del motor.
Nada de "apuesta", "esta cantado", "te aseguro". Siempre cierra con el
disclaimer corto de la seccion 10.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_OU_LINE = "2.5"
PY_TZ = ZoneInfo("America/Asuncion")

DISCLAIMER_SHORT = (
    "Análisis estadístico con fines informativos. No es consejo de apuesta "
    "ni garantía de resultado. +18. Jugá con cabeza, o ni juegues."
)

SALUDOS = ["Buenas.", "Hola, che.", "Dale, vamos."]

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _saludo_corto() -> str:
    return SALUDOS[0]


def _kickoff_local_py(kickoff_iso: str) -> str:
    dt = datetime.fromisoformat(kickoff_iso).astimezone(PY_TZ)
    dia = DIAS[dt.weekday()]
    return f"{dia} {dt.strftime('%H:%M')} (hora PY)"


def _one_liner_1x2(p_h: float, p_d: float, p_a: float) -> str:
    top = max(p_h, p_d, p_a)
    if top == p_h and p_h >= 0.55:
        return f"El modelo se inclina claro al local ({p_h:.0%}), pero el empate no es decoración ({p_d:.0%})."
    if top == p_a and p_a >= 0.55:
        return f"El modelo se inclina claro a la visita ({p_a:.0%})."
    if top < 0.40:
        return "Está parejo: acá el modelo no ve un favorito claro."
    return "Hay una tendencia, pero no una certeza. El fútbol siempre deja una rendija."


def _one_liner_btts(p_yes: float) -> str:
    if abs(p_yes - 0.5) <= 0.05:
        return f"Ambos marcan está {p_yes:.0%}–{1 - p_yes:.0%}. Moneda con saco y corbata."
    if p_yes > 0.5:
        return "Ambos marcan pinta con bastante marcha."
    return "Ambos marcan pinta más difícil que fácil."


def _one_liner_ou(p_over: float, line: str) -> str:
    if abs(p_over - 0.5) <= 0.05:
        return f"Over {line} está prácticamente mitad y mitad. No es una revelación."
    if p_over > 0.5:
        return f"El modelo ve más chances de que el partido se abra por encima de {line}."
    return f"El modelo ve un partido más bien cerrado, por debajo de {line}."


def render_paquete(prediction: dict, ou_line: str = DEFAULT_OU_LINE) -> str:
    """Arma el texto de paquete (1X2 + BTTS + O/U + top marcadores) a partir del
    JSON del motor (seccion 11.7). No inventa nada que no venga en el JSON."""
    markets = prediction["markets"]
    p_h, p_d, p_a = markets["1x2"]["H"], markets["1x2"]["D"], markets["1x2"]["A"]
    p_yes, p_no = markets["btts"]["yes"], markets["btts"]["no"]

    if ou_line not in markets["ou"]:
        raise ValueError(f"La linea {ou_line} no vino en el JSON del motor")
    p_over, p_under = markets["ou"][ou_line]["over"], markets["ou"][ou_line]["under"]

    cs_top = markets["cs_top"][:3]
    while len(cs_top) < 3:
        cs_top.append({"score": "—", "p": 0.0})

    factores = "\n".join(f"• {f}" for f in prediction["factors"])

    return (
        f"{_saludo_corto()}\n\n"
        f"*{prediction['home']} vs {prediction['away']}*\n"
        f"{prediction['competition_id']} · {_kickoff_local_py(prediction['kickoff'])}\n\n"
        f"*1X2*\n"
        f"Local: {p_h:.0%}\n"
        f"Empate: {p_d:.0%}\n"
        f"Visita: {p_a:.0%}\n"
        f"{_one_liner_1x2(p_h, p_d, p_a)}\n\n"
        f"*Ambos marcan*\n"
        f"Sí {p_yes:.0%} · No {p_no:.0%}\n"
        f"{_one_liner_btts(p_yes)}\n\n"
        f"*Goles (línea {ou_line})*\n"
        f"Más de {ou_line}: {p_over:.0%}\n"
        f"Menos de {ou_line}: {p_under:.0%}\n"
        f"{_one_liner_ou(p_over, ou_line)}\n\n"
        f"*Marcadores más probables*\n"
        f"1) {cs_top[0]['score']} ({cs_top[0]['p']:.0%})\n"
        f"2) {cs_top[1]['score']} ({cs_top[1]['p']:.0%})\n"
        f"3) {cs_top[2]['score']} ({cs_top[2]['p']:.0%})\n"
        f"Exacto es lotería: el primero igual suele ser minoría.\n\n"
        f"Confianza: {prediction['confidence']}\n"
        f"Por qué:\n{factores}\n\n"
        f"{DISCLAIMER_SHORT}"
    )
