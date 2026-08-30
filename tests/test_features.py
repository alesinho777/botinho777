import pandas as pd

from src.config import RHO_BOUNDS
from src.data.features import compute_league_ratings, load_matches

CSV_PATH = "data/raw/demo_matches.csv"
COMPETITION = "DEMO"


def test_rho_is_within_bounds_on_demo_csv():
    df = load_matches(CSV_PATH)
    ratings = compute_league_ratings(df, COMPETITION)
    assert RHO_BOUNDS[0] <= ratings.rho <= RHO_BOUNDS[1]


def _synthetic_matches(rows: list[tuple[str, str, int, int]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                "competition_id": "SYN",
                "season": "2024",
                "home_team_id": home,
                "away_team_id": away,
                "home_goals": hg,
                "away_goals": ag,
            }
            for i, (home, away, hg, ag) in enumerate(rows)
        ]
    )


def test_excess_low_scoring_draws_fits_negative_rho():
    teams = ["a", "b", "c", "d"]
    rows = []
    # Muchos cruces entre los 4 equipos, mayoria 0-0 o 1-1 (exceso deliberado
    # frente a lo que predice Poisson independiente con estos goles promedio).
    for i in range(30):
        home, away = teams[i % 4], teams[(i + 1) % 4]
        score = (0, 0) if i % 2 == 0 else (1, 1)
        rows.append((home, away, *score))

    df = _synthetic_matches(rows)
    ratings = compute_league_ratings(df, "SYN")

    assert ratings.rho < 0


def test_rho_falls_back_to_zero_without_low_score_matches():
    teams = ["a", "b", "c", "d"]
    rows = [(teams[i % 4], teams[(i + 1) % 4], 3, 2) for i in range(20)]
    df = _synthetic_matches(rows)

    ratings = compute_league_ratings(df, "SYN")
    assert ratings.rho == 0.0
