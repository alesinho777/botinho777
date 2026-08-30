import pandas as pd

from src.data.features import load_matches
from src.eval.historial import NO_HISTORIAL_TEXT, historial_summary
from src.eval.settle import save_settlement, settle_snapshot
from src.eval.snapshot import build_snapshot, save_snapshot

CSV_PATH = "data/raw/demo_matches.csv"
COMPETITION = "DEMO"


def _fake_prediction() -> dict:
    return {
        "fixture_id": "demo_2024-01-01_a_b",
        "kickoff": "2024-01-01T15:00:00+00:00",
        "competition_id": "DEMO",
        "home": "team_a",
        "away": "team_b",
        "lambda_home": 1.8,
        "lambda_away": 1.0,
        "markets": {
            "1x2": {"H": 0.55, "D": 0.25, "A": 0.20},
            "btts": {"yes": 0.60, "no": 0.40},
            "ou": {
                "1.5": {"over": 0.80, "under": 0.20},
                "2.5": {"over": 0.55, "under": 0.45},
                "3.5": {"over": 0.30, "under": 0.70},
            },
            "cs_top": [
                {"score": "2-1", "p": 0.12},
                {"score": "1-0", "p": 0.10},
                {"score": "1-1", "p": 0.09},
            ],
        },
        "factors": ["factor de prueba"],
        "confidence": "media",
        "model": "poisson_v1",
        "trained_until": "2023-12-31",
    }


def test_settle_snapshot_marks_hits_and_misses():
    prediction = _fake_prediction()

    settled_hit = settle_snapshot(prediction, actual_home_goals=2, actual_away_goals=1)
    assert settled_hit["hit_1x2"] is True  # pick del modelo era H
    assert settled_hit["hit_btts"] is True  # pick era yes, 2-1 tiene ambos marcan
    assert settled_hit["hit_ou_2.5"] is True  # pick era over, 2+1=3 > 2.5
    assert settled_hit["hit_exact_top1"] is True  # 2-1 es el top 1
    assert settled_hit["actual_score"] == "2-1"

    settled_miss = settle_snapshot(prediction, actual_home_goals=0, actual_away_goals=1)
    assert settled_miss["hit_1x2"] is False  # pick era H, gano A
    assert settled_miss["hit_btts"] is False  # pick era yes, 0-1 no tiene ambos marcan
    assert settled_miss["hit_ou_2.5"] is False  # pick era over, 0+1=1 < 2.5
    assert settled_miss["hit_exact_top3"] is False  # 0-1 no esta en el top 3


def test_historial_summary_honest_when_no_data(tmp_path):
    missing_path = tmp_path / "no_existe.csv"
    assert historial_summary(str(missing_path)) == NO_HISTORIAL_TEXT


def test_historial_summary_aggregates_settlements(tmp_path):
    results_csv = tmp_path / "settlements.csv"
    prediction = _fake_prediction()

    settled_1 = settle_snapshot(prediction, actual_home_goals=2, actual_away_goals=1)
    settled_1["fixture_id"] = "fixture_1"
    save_settlement(settled_1, out_path=str(results_csv))

    settled_2 = settle_snapshot(prediction, actual_home_goals=0, actual_away_goals=1)
    settled_2["fixture_id"] = "fixture_2"
    save_settlement(settled_2, out_path=str(results_csv))

    text = historial_summary(str(results_csv))
    assert "Partidos evaluados: 2" in text
    assert "Acierto 1X2: 50%" in text
    assert "transparencia del modelo" in text


def test_build_snapshot_uses_only_data_before_as_of(tmp_path):
    df = load_matches(CSV_PATH)
    subset = df[df["competition_id"] == COMPETITION].sort_values("date")
    row = subset.iloc[100]
    as_of = row["date"]

    prediction = build_snapshot(
        df,
        COMPETITION,
        row["home_team_id"],
        row["away_team_id"],
        as_of=as_of,
        kickoff_iso=as_of.isoformat(),
    )

    assert pd.Timestamp(prediction["trained_until"]) <= as_of
    assert set(prediction["markets"]["1x2"].keys()) == {"H", "D", "A"}

    path = save_snapshot(prediction, out_dir=str(tmp_path))
    assert (tmp_path / f"{as_of.date().isoformat()}.json").exists()
    assert path.endswith(".json")
