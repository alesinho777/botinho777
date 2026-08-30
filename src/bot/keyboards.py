"""Teclados inline (seccion 7.3 del spec, nivel 1 y nivel 3 recortado al partido demo)."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CB_PARTIDOS_HOY = "partidos_hoy"
CB_ELEGIR_LIGA = "elegir_liga"
CB_COMO_FUNCIONA = "como_funciona"
CB_PLANES = "planes"
CB_PAQUETE_DEMO = "paquete_demo"


def home_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Partidos de hoy", callback_data=CB_PARTIDOS_HOY)],
            [InlineKeyboardButton("Elegir liga", callback_data=CB_ELEGIR_LIGA)],
            [InlineKeyboardButton("Cómo funciona", callback_data=CB_COMO_FUNCIONA)],
            [InlineKeyboardButton("Plan premium", callback_data=CB_PLANES)],
        ]
    )


def partido_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Paquete", callback_data=CB_PAQUETE_DEMO)]])
