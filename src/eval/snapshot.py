"""Snapshots pre-partido (seccion 11.9 del spec).

No modifica poisson.py/markets.py/predict.py/render.py: solo los reusa con un
`as_of` explicito, para poder generar predicciones "como si fuera esa fecha"
sin mirar partidos futuros (nada de leakage al hacer backtest/settle).
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import pandas as pd

from src.data.features import build_factors, compute_league_ratings, expected_goals
from src.model.markets import confidence_level, market_1x2, market_btts, market_ou_all, top_correct_scores
from src.model.poisson import score_matrix

MODEL_NAME = "poisson_v1"
DEFAULT_PREDICTIONS_DIR = "data/predictions"


def build_snapshot(
    df: pd.DataFrame,
    competition_id: str,
    home_team_id: str,
    away_team_id: str,
    as_of: datetime,
    kickoff_iso: str,
) -> dict:
    """Arma el mismo JSON de prediccion (seccion 11.7) pero con ratings calculados
    SOLO con partidos anteriores a `as_of` (corte temporal explicito)."""
    ratings = compute_league_ratings(df, competition_id, as_of=as_of)

    lambda_home, lambda_away = expected_goals(ratings, home_team_id, away_team_id)
    matrix = score_matrix(lambda_home, lambda_away, rho=ratings.rho)

    probs_1x2 = market_1x2(matrix)
    probs_btts = market_btts(matrix)
    probs_ou = market_ou_all(matrix)
    top_scores = top_correct_scores(matrix, top_n=3)
    confidence = confidence_level(probs_1x2, lambda_home, lambda_away)
    factors = build_factors(ratings, home_team_id, away_team_id)

    fixture_id = f"{competition_id.lower()}_{kickoff_iso[:10]}_{home_team_id}_{away_team_id}"
    return {
        "fixture_id": fixture_id,
        "kickoff": kickoff_iso,
        "competition_id": competition_id,
        "home": home_team_id,
        "away": away_team_id,
        "lambda_home": round(lambda_home, 2),
        "lambda_away": round(lambda_away, 2),
        "markets": {
            "1x2": probs_1x2,
            "btts": probs_btts,
            "ou": probs_ou,
            "cs_top": top_scores,
        },
        "factors": factors,
        "confidence": confidence,
        "model": MODEL_NAME,
        "trained_until": ratings.as_of.date().isoformat(),
    }


def save_snapshot(prediction: dict, out_dir: str = DEFAULT_PREDICTIONS_DIR) -> str:
    """Guarda/actualiza el snapshot del dia de kickoff en data/predictions/YYYY-MM-DD.json
    (una lista de fixtures de ese dia; se puede llamar varias veces sin duplicar)."""
    os.makedirs(out_dir, exist_ok=True)
    day = prediction["kickoff"][:10]
    path = os.path.join(out_dir, f"{day}.json")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            snapshots = json.load(f)
    else:
        snapshots = []

    snapshots = [s for s in snapshots if s["fixture_id"] != prediction["fixture_id"]]
    snapshots.append(prediction)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, indent=2, ensure_ascii=False)
    return path
