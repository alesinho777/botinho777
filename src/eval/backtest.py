"""CLI de backtest ilustrativo (seccion 16.8 del spec): genera snapshots + settle
sobre partidos YA JUGADOS del CSV, usando en cada uno SOLO el historial anterior
a esa fecha (as_of = fecha del partido), para poder mostrar /historial sin
esperar a que se jueguen partidos reales.

Uso:
    python -m src.eval.backtest --n 30
"""
from __future__ import annotations

import argparse

from src.data.features import load_matches
from src.eval.historial import historial_summary
from src.eval.settle import DEFAULT_RESULTS_CSV, save_settlement, settle_snapshot
from src.eval.snapshot import DEFAULT_PREDICTIONS_DIR, build_snapshot, save_snapshot
from src.model.predict import DEFAULT_COMPETITION, DEFAULT_CSV


def run_backtest(
    csv_path: str = DEFAULT_CSV,
    competition_id: str = DEFAULT_COMPETITION,
    n: int = 30,
    predictions_dir: str = DEFAULT_PREDICTIONS_DIR,
    results_csv: str = DEFAULT_RESULTS_CSV,
) -> int:
    df = load_matches(csv_path)
    subset = df[df["competition_id"] == competition_id].sort_values("date")
    to_evaluate = subset.tail(n)

    settled = 0
    for _, row in to_evaluate.iterrows():
        as_of = row["date"]
        kickoff_iso = row["date"].isoformat()
        try:
            prediction = build_snapshot(
                df, competition_id, row["home_team_id"], row["away_team_id"], as_of, kickoff_iso
            )
        except ValueError:
            # Sin historial previo suficiente para este partido todavia (arranque de liga).
            continue

        save_snapshot(prediction, out_dir=predictions_dir)
        settlement = settle_snapshot(prediction, int(row["home_goals"]), int(row["away_goals"]))
        save_settlement(settlement, out_path=results_csv)
        settled += 1

    return settled


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest ilustrativo: snapshot + settle sobre el CSV demo")
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument("--competition", default=DEFAULT_COMPETITION)
    parser.add_argument("--n", type=int, default=30, help="cuantos de los ultimos partidos evaluar")
    parser.add_argument("--results-csv", default=DEFAULT_RESULTS_CSV)
    args = parser.parse_args()

    settled = run_backtest(args.csv, args.competition, args.n, results_csv=args.results_csv)
    print(f"Settled {settled} partidos de backtest.\n")
    print(historial_summary(args.results_csv))


if __name__ == "__main__":
    main()
