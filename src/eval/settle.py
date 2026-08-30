"""Settlement: compara un snapshot pre-partido contra el resultado real (seccion 11.9-11.10).

Nunca recalcula la prediccion con el resultado ya sabido: toma el snapshot tal
cual se guardo antes del partido y solo lo contrasta con el marcador final.
"""
from __future__ import annotations

import csv
import os

DEFAULT_RESULTS_CSV = "data/results/settlements.csv"

FIELDNAMES = [
    "fixture_id",
    "competition_id",
    "home",
    "away",
    "kickoff",
    "actual_score",
    "hit_1x2",
    "hit_btts",
    "hit_ou_1.5",
    "hit_ou_2.5",
    "hit_ou_3.5",
    "hit_exact_top1",
    "hit_exact_top3",
    "model",
]


def _top_pick(probs: dict[str, float]) -> str:
    return max(probs, key=probs.get)


def settle_snapshot(prediction: dict, actual_home_goals: int, actual_away_goals: int) -> dict:
    """Devuelve una fila de settlement: por cada mercado, si el pick del modelo
    (la opcion de mayor probabilidad en el snapshot) acerto contra el resultado real."""
    if actual_home_goals > actual_away_goals:
        actual_1x2 = "H"
    elif actual_home_goals < actual_away_goals:
        actual_1x2 = "A"
    else:
        actual_1x2 = "D"

    actual_btts = "yes" if actual_home_goals >= 1 and actual_away_goals >= 1 else "no"
    total_goals = actual_home_goals + actual_away_goals
    actual_score = f"{actual_home_goals}-{actual_away_goals}"

    markets = prediction["markets"]
    ou_hits = {}
    for line_str, probs in markets["ou"].items():
        actual_side = "over" if total_goals > float(line_str) else "under"
        ou_hits[line_str] = _top_pick(probs) == actual_side

    predicted_scores = [cs["score"] for cs in markets["cs_top"]]

    return {
        "fixture_id": prediction["fixture_id"],
        "competition_id": prediction["competition_id"],
        "home": prediction["home"],
        "away": prediction["away"],
        "kickoff": prediction["kickoff"],
        "actual_score": actual_score,
        "hit_1x2": _top_pick(markets["1x2"]) == actual_1x2,
        "hit_btts": _top_pick(markets["btts"]) == actual_btts,
        "hit_ou_1.5": ou_hits.get("1.5", False),
        "hit_ou_2.5": ou_hits.get("2.5", False),
        "hit_ou_3.5": ou_hits.get("3.5", False),
        "hit_exact_top1": bool(predicted_scores) and predicted_scores[0] == actual_score,
        "hit_exact_top3": actual_score in predicted_scores,
        "model": prediction["model"],
    }


def save_settlement(settlement: dict, out_path: str = DEFAULT_RESULTS_CSV) -> str:
    """Agrega una fila al CSV de settlements (crea el archivo con header si no existe,
    y reemplaza la fila si el mismo fixture_id ya estaba settled)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    rows: list[dict] = []
    if os.path.exists(out_path):
        with open(out_path, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    rows = [r for r in rows if r["fixture_id"] != settlement["fixture_id"]]
    rows.append({k: settlement[k] for k in FIELDNAMES})

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return out_path
