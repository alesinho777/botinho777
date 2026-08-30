"""Handlers minimos del bot (secciones 16.6 y 16.8 del spec).

/start, el partido DEMO -> paquete, y /historial (hit-rate publico de
settlements). Todavia sin tope free ni roles/`grant` (seccion 16.7): eso
necesita user_id reales de Telegram.
"""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.copy import COMO_FUNCIONA_TEXT, LIGA_NO_CUBIERTA_TEXT, PLANES_TEXT, START_TEXT
from src.bot.keyboards import (
    CB_COMO_FUNCIONA,
    CB_ELEGIR_LIGA,
    CB_PAQUETE_DEMO,
    CB_PARTIDOS_HOY,
    CB_PLANES,
    home_menu,
    partido_menu,
)
from src.eval.historial import historial_summary
from src.model.predict import DEFAULT_COMPETITION, DEFAULT_CSV, build_prediction
from src.nlp.render import render_paquete

DEMO_HOME = "demo_team_01"
DEMO_AWAY = "demo_team_02"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_TEXT, reply_markup=home_menu())


async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(historial_summary())


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == CB_PARTIDOS_HOY:
        text = (
            f"{DEMO_HOME} vs {DEMO_AWAY}\n"
            f"Partido de demostración (competencia {DEFAULT_COMPETITION})\n\n"
            "Todavía no tengo fixtures reales cargados, así que te muestro cómo\n"
            "responde el motor con este cruce de ejemplo."
        )
        await query.message.reply_text(text, reply_markup=partido_menu())
    elif query.data == CB_ELEGIR_LIGA:
        await query.message.reply_text(LIGA_NO_CUBIERTA_TEXT)
    elif query.data == CB_COMO_FUNCIONA:
        await query.message.reply_text(COMO_FUNCIONA_TEXT)
    elif query.data == CB_PLANES:
        await query.message.reply_text(PLANES_TEXT)
    elif query.data == CB_PAQUETE_DEMO:
        prediction = build_prediction(DEFAULT_CSV, DEFAULT_COMPETITION, DEMO_HOME, DEMO_AWAY)
        text = render_paquete(prediction)
        await query.message.reply_text(text, parse_mode="Markdown")
