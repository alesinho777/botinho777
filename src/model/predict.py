"""CLI de prediccion (seccion 16.4 del spec).

Uso:
    python -m src.model.predict --home demo_team_01 --away demo_team_02
    python -m src.model.predict --home demo_team_01 --away demo_team_02 \
        --csv data/raw/demo_matches.csv --competition DEMO
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from src.data.features import build_factors, compute_league_ratings, expected_goals, load_matches
from src.model.markets import confidence_level, market_1x2, market_btts, market_ou_all, top_correct_scores
from src.model.poisson import score_matrix

DEFAULT_CSV = "data/raw/demo_matches.csv"
DEFAULT_COMPETITION = "DEMO"
MODEL_NAME = "poisson_v1"


def build_prediction(
    csv_path: str,
    competition_id: str,
    home_team_id: str,
    away_team_id: str,
) -> dict:
    df = load_matches(csv_path)
    ratings = compute_league_ratings(df, competition_id)

    lambda_home, lambda_away = expected_goals(ratings, home_team_id, away_team_id)
    matrix = score_matrix(lambda_home, lambda_away, rho=ratings.rho)

    probs_1x2 = market_1x2(matrix)
    probs_btts = market_btts(matrix)
    probs_ou = market_ou_all(matrix)
    top_scores = top_correct_scores(matrix, top_n=3)
    confidence = confidence_level(probs_1x2, lambda_home, lambda_away)
    factors = build_factors(ratings, home_team_id, away_team_id)

    now = datetime.now(timezone.utc)
    return {
        "fixture_id": f"{competition_id.lower()}_{now.date().isoformat()}_{home_team_id}_{away_team_id}",
        "kickoff": now.isoformat(),
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Prediccion Poisson para un partido (Botinho777)")
    parser.add_argument("--home", required=True, help="team_id del equipo local")
    parser.add_argument("--away", required=True, help="team_id del equipo visitante")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="CSV de historial de partidos")
    parser.add_argument("--competition", default=DEFAULT_COMPETITION, help="competition_id")
    args = parser.parse_args()

    prediction = build_prediction(args.csv, args.competition, args.home, args.away)
    print(json.dumps(prediction, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
