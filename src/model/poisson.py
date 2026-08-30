"""Motor Poisson independiente + correccion Dixon-Coles (seccion 11.4 y 11.5
del spec, fase 1.5: "multiplicar P(0-0), P(1-0), P(0-1), P(1-1) por factor rho").

De lambda_home y lambda_away se arma una matriz de probabilidades de marcador
0..MAX_GOALS x 0..MAX_GOALS. Todos los mercados (1x2, btts, ou, exacto) se
derivan de esta MISMA matriz para que sean consistentes entre si.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import poisson

from src.config import CLAMP_LAMBDA_MAX, CLAMP_LAMBDA_MIN, MAX_GOALS


def clamp_lambda(value: float) -> float:
    return min(max(value, CLAMP_LAMBDA_MIN), CLAMP_LAMBDA_MAX)


def dixon_coles_tau(x: int, y: int, lambda_home: float, lambda_away: float, rho: float) -> float:
    """Factor de correccion Dixon-Coles para los 4 marcadores bajos donde
    Poisson independiente esta sesgado; 1.0 (sin efecto) para cualquier otro
    marcador."""
    if x == 0 and y == 0:
        return 1.0 - lambda_home * lambda_away * rho
    if x == 0 and y == 1:
        return 1.0 + lambda_home * rho
    if x == 1 and y == 0:
        return 1.0 + lambda_away * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(
    lambda_home: float, lambda_away: float, max_goals: int = MAX_GOALS, rho: float = 0.0
) -> np.ndarray:
    """Devuelve una matriz (max_goals+1) x (max_goals+1) de P(home=g, away=h),
    renormalizada para que la suma del grid sea exactamente 1 (la cola > max_goals
    se reparte proporcionalmente al renormalizar). Con rho != 0 aplica la
    correccion Dixon-Coles sobre los 4 marcadores bajos antes de renormalizar."""
    lh = clamp_lambda(lambda_home)
    la = clamp_lambda(lambda_away)

    goals = np.arange(0, max_goals + 1)
    p_home = poisson.pmf(goals, lh)
    p_away = poisson.pmf(goals, la)

    matrix = np.outer(p_home, p_away)

    if rho != 0.0:
        for x in (0, 1):
            for y in (0, 1):
                tau = dixon_coles_tau(x, y, lh, la, rho)
                matrix[x, y] *= max(tau, 0.0)

    total = matrix.sum()
    if total <= 0:
        raise ValueError("La matriz de marcadores sumo 0; revisa lambda_home/lambda_away")
    return matrix / total
