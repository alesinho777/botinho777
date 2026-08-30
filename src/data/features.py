"""Ratings att/def por equipo a partir de historial (seccion 11.3, Opcion A del spec).

Solo usa partidos con date < as_of (nada de futuro). Suaviza equipos con pocos
partidos hacia 1.0 y aplica decaimiento exponencial por antiguedad.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import datetime

import pandas as pd
from scipy.optimize import minimize_scalar

from src.config import DECAY_HALF_LIFE_DAYS, DEFAULT_HOME_ADV, RHO_BOUNDS, SMOOTHING_K
from src.model.poisson import dixon_coles_tau


@dataclass(frozen=True)
class TeamRatings:
    att_home: float
    def_home: float
    att_away: float
    def_away: float
    games_played: int


@dataclass(frozen=True)
class LeagueRatings:
    competition_id: str
    as_of: datetime
    league_avg_home_goals: float
    league_avg_away_goals: float
    home_adv: float
    rho: float
    teams: dict[str, TeamRatings]


def load_matches(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    required = {
        "date",
        "competition_id",
        "season",
        "home_team_id",
        "away_team_id",
        "home_goals",
        "away_goals",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en {csv_path}: {sorted(missing)}")
    return df


def _decay_weight(days_ago: pd.Series) -> pd.Series:
    return 0.5 ** (days_ago / DECAY_HALF_LIFE_DAYS)


def compute_league_ratings(
    df: pd.DataFrame,
    competition_id: str,
    as_of: datetime | None = None,
    home_adv: float = DEFAULT_HOME_ADV,
    k: int = SMOOTHING_K,
) -> LeagueRatings:
    matches = df[df["competition_id"] == competition_id].copy()
    if as_of is not None:
        matches = matches[matches["date"] < as_of]
    if matches.empty:
        raise ValueError(f"No hay partidos historicos para {competition_id} antes de {as_of}")

    as_of = as_of or matches["date"].max() + pd.Timedelta(days=1)
    matches["days_ago"] = (as_of - matches["date"]).dt.total_seconds() / 86400.0
    matches["weight"] = _decay_weight(matches["days_ago"])

    league_avg_home_goals = float(
        (matches["home_goals"] * matches["weight"]).sum() / matches["weight"].sum()
    )
    league_avg_away_goals = float(
        (matches["away_goals"] * matches["weight"]).sum() / matches["weight"].sum()
    )

    teams: dict[str, TeamRatings] = {}
    team_ids = set(matches["home_team_id"]) | set(matches["away_team_id"])
    for team_id in team_ids:
        home_rows = matches[matches["home_team_id"] == team_id]
        away_rows = matches[matches["away_team_id"] == team_id]

        n_home = float(home_rows["weight"].sum())
        n_away = float(away_rows["weight"].sum())

        att_home_raw = (
            (home_rows["home_goals"] * home_rows["weight"]).sum() / n_home / league_avg_home_goals
            if n_home > 0
            else 1.0
        )
        def_home_raw = (
            (home_rows["away_goals"] * home_rows["weight"]).sum() / n_home / league_avg_away_goals
            if n_home > 0
            else 1.0
        )
        att_away_raw = (
            (away_rows["away_goals"] * away_rows["weight"]).sum() / n_away / league_avg_away_goals
            if n_away > 0
            else 1.0
        )
        def_away_raw = (
            (away_rows["home_goals"] * away_rows["weight"]).sum() / n_away / league_avg_home_goals
            if n_away > 0
            else 1.0
        )

        def smooth(raw: float, n: float) -> float:
            return (n * raw + k * 1.0) / (n + k)

        teams[team_id] = TeamRatings(
            att_home=smooth(att_home_raw, n_home),
            def_home=smooth(def_home_raw, n_home),
            att_away=smooth(att_away_raw, n_away),
            def_away=smooth(def_away_raw, n_away),
            games_played=int(len(home_rows) + len(away_rows)),
        )

    preliminary = LeagueRatings(
        competition_id=competition_id,
        as_of=as_of,
        league_avg_home_goals=league_avg_home_goals,
        league_avg_away_goals=league_avg_away_goals,
        home_adv=home_adv,
        rho=0.0,
        teams=teams,
    )
    rho = _estimate_rho(matches, preliminary)
    return replace(preliminary, rho=rho)


def _estimate_rho(matches: pd.DataFrame, ratings: LeagueRatings) -> float:
    """Ajusta el parametro Dixon-Coles (seccion 11.5) por maxima verosimilitud,
    dejando fijas las ratings att/def/home_adv ya calculadas (fase 1.5 del spec,
    no el modelo Option B completo). Como tau=1 fuera de los 4 marcadores bajos,
    la log-verosimilitud solo depende de esas filas."""
    low_score = matches[
        ((matches["home_goals"] <= 1) & (matches["away_goals"] <= 1))
    ]
    if low_score.empty:
        return 0.0

    rows = [
        (
            int(row["home_goals"]),
            int(row["away_goals"]),
            *expected_goals(ratings, row["home_team_id"], row["away_team_id"]),
            float(row["weight"]),
        )
        for _, row in low_score.iterrows()
    ]

    def neg_log_likelihood(rho: float) -> float:
        total = 0.0
        for x, y, lambda_home, lambda_away, weight in rows:
            tau = dixon_coles_tau(x, y, lambda_home, lambda_away, rho)
            total += weight * math.log(max(tau, 1e-10))
        return -total

    result = minimize_scalar(neg_log_likelihood, bounds=RHO_BOUNDS, method="bounded")
    if not result.success:
        return 0.0
    return float(result.x)


def expected_goals(ratings: LeagueRatings, home_team_id: str, away_team_id: str) -> tuple[float, float]:
    """lambda_home, lambda_away segun seccion 11.4 del spec."""
    if home_team_id not in ratings.teams:
        raise ValueError(f"Equipo desconocido en {ratings.competition_id}: {home_team_id}")
    if away_team_id not in ratings.teams:
        raise ValueError(f"Equipo desconocido en {ratings.competition_id}: {away_team_id}")

    home = ratings.teams[home_team_id]
    away = ratings.teams[away_team_id]

    lambda_home = ratings.league_avg_home_goals * home.att_home * away.def_away * ratings.home_adv
    lambda_away = ratings.league_avg_away_goals * away.att_away * home.def_home
    return lambda_home, lambda_away


def build_factors(ratings: LeagueRatings, home_team_id: str, away_team_id: str) -> list[str]:
    """Factores en base a reglas simples comparando att/def contra la media de liga
    (seccion 11.7 del spec: el motor arma los factores, el LLM no inventa ninguno)."""
    home = ratings.teams[home_team_id]
    away = ratings.teams[away_team_id]
    factors: list[str] = []

    if home.att_home > away.att_away:
        factors.append(f"{home_team_id} tiene mejor ataque suavizado que {away_team_id} en la ventana")
    elif away.att_away > home.att_home:
        factors.append(f"{away_team_id} tiene mejor ataque suavizado que {home_team_id} en la ventana")

    if away.def_away < 1.0:
        factors.append(f"{away_team_id} concede menos de la media de liga como visita")
    if home.def_home < 1.0:
        factors.append(f"{home_team_id} concede menos de la media de liga como local")

    factors.append(f"Ventaja de local aplicada: {ratings.home_adv:.2f}")
    return factors
