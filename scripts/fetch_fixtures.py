"""
Baja los proximos partidos programados (status=SCHEDULED) desde football-data.org
para las 4 ligas europeas soportadas, y arma data/raw/upcoming_fixtures.csv con
columnas: kickoff_utc,competition_id,home_team_id,home_team_name,away_team_id,
away_team_name.

Se corre por separado de fetch_real_data.py (que baja el HISTORIAL de partidos
terminados, usado para calcular ratings): este script solo trae el calendario
de partidos que todavia no se jugaron, para que la web pueda listar "los
partidos del dia / de la semana / del mes" en vez de dejar elegir cualquier
cruce a mano.

Requiere FOOTBALL_DATA_API_KEY en .env (mismo plan gratis de fetch_real_data.py).

Uso:
    python -m scripts.fetch_fixtures
    python -m scripts.fetch_fixtures --days 14
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import date, timedelta

import requests

from src.config import load_settings
from scripts.fetch_real_data import API_BASE, COMPETITIONS, slugify

OUT_PATH = "data/raw/upcoming_fixtures.csv"


def fetch_upcoming(code: str, api_key: str, date_from: str, date_to: str) -> list[dict]:
    headers = {"X-Auth-Token": api_key}
    resp = requests.get(
        f"{API_BASE}/competitions/{code}/matches",
        headers=headers,
        params={"dateFrom": date_from, "dateTo": date_to, "status": "SCHEDULED"},
        timeout=20,
    )
    if resp.status_code == 429:
        print("  Rate limit alcanzado, esperando 60s...")
        time.sleep(60)
        resp = requests.get(
            f"{API_BASE}/competitions/{code}/matches",
            headers=headers,
            params={"dateFrom": date_from, "dateTo": date_to, "status": "SCHEDULED"},
            timeout=20,
        )
    if resp.status_code != 200:
        print(f"  Sin acceso ({resp.status_code}), se omite {code}.")
        return []

    rows = []
    for m in resp.json().get("matches", []):
        rows.append(
            {
                "kickoff_utc": m["utcDate"],
                "competition_id": COMPETITIONS[code],
                "home_team_id": slugify(m["homeTeam"]["name"]),
                "home_team_name": m["homeTeam"]["name"],
                "away_team_id": slugify(m["awayTeam"]["name"]),
                "away_team_name": m["awayTeam"]["name"],
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--competitions",
        nargs="+",
        default=list(COMPETITIONS.keys()),
        choices=list(COMPETITIONS.keys()),
        help="Codigos football-data.org a bajar (default: todos los soportados)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=35,
        help="Cuantos dias hacia adelante traer (default 35, ~el mes en curso)",
    )
    args = parser.parse_args()

    settings = load_settings()
    if not settings.football_data_api_key:
        print(
            "Falta FOOTBALL_DATA_API_KEY en .env. Sacala gratis en "
            "https://www.football-data.org/client/register y ponela en .env.",
            file=sys.stderr,
        )
        sys.exit(1)

    date_from = date.today().isoformat()
    date_to = (date.today() + timedelta(days=args.days)).isoformat()

    all_rows: list[dict] = []
    for code in args.competitions:
        print(f"Bajando calendario de {COMPETITIONS[code]} ({code})...")
        rows = fetch_upcoming(code, settings.football_data_api_key, date_from, date_to)
        print(f"  {len(rows)} partidos programados.")
        all_rows.extend(rows)
        time.sleep(6)  # plan free: 10 req/min

    all_rows.sort(key=lambda r: r["kickoff_utc"])

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "kickoff_utc",
                "competition_id",
                "home_team_id",
                "home_team_name",
                "away_team_id",
                "away_team_name",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nListos {len(all_rows)} partidos programados en {OUT_PATH}")


if __name__ == "__main__":
    main()
