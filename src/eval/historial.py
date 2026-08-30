"""Texto de /historial: hit-rate PUBLICO del modelo, a partir de settlement de
snapshots pre-partido (seccion 11.10 del spec). No recalcula nada a posteriori:
solo agrega lo que ya quedo guardado en el CSV de settlements."""
from __future__ import annotations

import os

import pandas as pd

from src.eval.settle import DEFAULT_RESULTS_CSV

NO_HISTORIAL_TEXT = (
    "Todavía no tengo historial de settlement. Preferible admitirlo a inventar un "
    "porcentaje. En cuanto se liquiden pronósticos pre-partido, esto se llena solo."
)


def historial_summary(results_csv: str = DEFAULT_RESULTS_CSV) -> str:
    if not os.path.exists(results_csv):
        return NO_HISTORIAL_TEXT

    df = pd.read_csv(results_csv)
    if df.empty:
        return NO_HISTORIAL_TEXT

    n = len(df)
    acc_1x2 = df["hit_1x2"].mean()
    acc_btts = df["hit_btts"].mean()
    acc_ou25 = df["hit_ou_2.5"].mean()
    acc_exact_top3 = df["hit_exact_top3"].mean()

    return (
        f"Historial del modelo (settlement de pronósticos pre-partido)\n\n"
        f"Partidos evaluados: {n}\n"
        f"Acierto 1X2: {acc_1x2:.0%}\n"
        f"Acierto ambos marcan: {acc_btts:.0%}\n"
        f"Acierto over/under 2.5: {acc_ou25:.0%}\n"
        f"El resultado real estuvo en el top 3 de marcadores: {acc_exact_top3:.0%}\n\n"
        "Esto es transparencia del modelo, no promesa de resultados futuros."
    )
