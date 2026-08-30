"""
Genera data/raw/demo_matches.csv: partidos sinteticos de una liga de demostracion
(10 equipos, 3 temporadas round-robin ida y vuelta) para poder correr el repo offline.
NO representa una liga real. Uso: python scripts/generate_demo_csv.py
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta

random.seed(7)

COMPETITION_ID = "DEMO"
TEAMS = [f"demo_team_{i:02d}" for i in range(1, 11)]

# Fuerzas de ataque/defensa "verdaderas" ocultas, usadas solo para simular resultados.
TRUE_ATT = {t: random.uniform(0.7, 1.4) for t in TEAMS}
TRUE_DEF = {t: random.uniform(0.7, 1.4) for t in TEAMS}
LEAGUE_AVG_HOME_GOALS = 1.45
LEAGUE_AVG_AWAY_GOALS = 1.15
HOME_ADV = 1.25


def sample_poisson(lam: float) -> int:
    # Knuth's algorithm, evita depender de numpy en el script de generacion.
    l = pow(2.718281828459045, -lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= l:
            return k - 1


def round_robin(teams: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for i, home in enumerate(teams):
        for j, away in enumerate(teams):
            if i != j:
                pairs.append((home, away))
    return pairs


def main() -> None:
    rows = []
    start = date(2023, 8, 1)
    current = start
    for season in ("2023-24", "2024-25", "2025-26"):
        fixtures = round_robin(TEAMS)
        random.shuffle(fixtures)
        for home, away in fixtures:
            lam_h = LEAGUE_AVG_HOME_GOALS * TRUE_ATT[home] * TRUE_DEF[away] * HOME_ADV
            lam_a = LEAGUE_AVG_AWAY_GOALS * TRUE_ATT[away] * TRUE_DEF[home]
            hg = sample_poisson(lam_h)
            ag = sample_poisson(lam_a)
            rows.append(
                {
                    "date": current.isoformat(),
                    "competition_id": COMPETITION_ID,
                    "season": season,
                    "home_team_id": home,
                    "away_team_id": away,
                    "home_goals": hg,
                    "away_goals": ag,
                }
            )
            current += timedelta(days=1)

    out_path = "data/raw/demo_matches.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "competition_id",
                "season",
                "home_team_id",
                "away_team_id",
                "home_goals",
                "away_goals",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Escritas {len(rows)} filas en {out_path}")


if __name__ == "__main__":
    main()
