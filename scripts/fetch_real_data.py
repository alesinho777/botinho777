"""
Baja historial real de partidos terminados desde football-data.org (v4) para
las ligas europeas soportadas y arma data/raw/real_matches.csv en el mismo
formato que usa el motor (date,competition_id,season,home_team_id,
away_team_id,home_goals,away_goals).

Requiere FOOTBALL_DATA_API_KEY en .env (plan gratis: https://www.football-data.org/client/register).

Uso:
    python scripts/fetch_real_data.py
    python scripts/fetch_real_data.py --competitions CL PL
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import unicodedata

import requests

from src.config import load_settings

API_BASE = "https://api.football-data.org/v4"

# Codigos de football-data.org -> competition_id interno del proyecto.
COMPETITIONS = {
    "CL": "CHAMPIONS",
    "PD": "LALIGA",
    "PL": "PREMIER",
    "SA": "SERIEA",
}

OUT_PATH = "data/raw/real_matches.csv"


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
    return slug


def fetch_competition(code: str, api_key: str, seasons_back: int) -> list[dict]:
    headers = {"X-Auth-Token": api_key}
    rows: list[dict] = []
    comp_resp = requests.get(f"{API_BASE}/competitions/{code}", headers=headers, timeout=15)
    comp_resp.raise_for_status()
    current_season_start_year = comp_resp.json()["currentSeason"]["startDate"][:4]

    for offset in range(seasons_back):
        season_year = int(current_season_start_year) - offset
        resp = requests.get(
            f"{API_BASE}/competitions/{code}/matches",
            headers=headers,
            params={"season": season_year, "status": "FINISHED"},
            timeout=20,
        )
        if resp.status_code == 429:
            print("  Rate limit alcanzado, esperando 60s...")
            time.sleep(60)
            resp = requests.get(
                f"{API_BASE}/competitions/{code}/matches",
                headers=headers,
                params={"season": season_year, "status": "FINISHED"},
                timeout=20,
            )
        if resp.status_code != 200:
            print(f"  Temporada {season_year}: sin acceso ({resp.status_code}), se omite.")
            continue

        matches = resp.json().get("matches", [])
        for m in matches:
            score = m["score"]["fullTime"]
            if score["home"] is None or score["away"] is None:
                continue
            rows.append(
                {
                    "date": m["utcDate"][:10],
                    "competition_id": COMPETITIONS[code],
                    "season": f"{season_year}-{str(season_year + 1)[-2:]}",
                    "home_team_id": slugify(m["homeTeam"]["name"]),
                    "home_team_name": m["homeTeam"]["name"],
                    "away_team_id": slugify(m["awayTeam"]["name"]),
                    "away_team_name": m["awayTeam"]["name"],
                    "home_goals": score["home"],
                    "away_goals": score["away"],
                }
            )
        print(f"  Temporada {season_year}: {len(matches)} partidos.")
        time.sleep(6)  # plan free: 10 req/min

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
        "--seasons-back",
        type=int,
        default=3,
        help="Cuantas temporadas hacia atras bajar por competicion (default 3)",
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

    all_rows: list[dict] = []
    for code in args.competitions:
        print(f"Bajando {COMPETITIONS[code]} ({code})...")
        all_rows.extend(fetch_competition(code, settings.football_data_api_key, args.seasons_back))

    all_rows.sort(key=lambda r: r["date"])

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "competition_id",
                "season",
                "home_team_id",
                "home_team_name",
                "away_team_id",
                "away_team_name",
                "home_goals",
                "away_goals",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nListas {len(all_rows)} filas en {OUT_PATH}")


if __name__ == "__main__":
    main()
