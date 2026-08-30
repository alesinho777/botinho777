"""Deriva todos los mercados de la misma matriz de marcadores (seccion 11.6 del spec)."""
from __future__ import annotations

import numpy as np

OU_LINES = (1.5, 2.5, 3.5)


def market_1x2(matrix: np.ndarray) -> dict[str, float]:
    n = matrix.shape[0]
    idx = np.arange(n)
    p_h = float(matrix[np.greater.outer(idx, idx)].sum())
    p_d = float(np.trace(matrix))
    p_a = float(matrix[np.less.outer(idx, idx)].sum())
    return {"H": p_h, "D": p_d, "A": p_a}


def market_btts(matrix: np.ndarray) -> dict[str, float]:
    p_yes = float(matrix[1:, 1:].sum())
    return {"yes": p_yes, "no": 1.0 - p_yes}


def market_ou(matrix: np.ndarray, line: float) -> dict[str, float]:
    n = matrix.shape[0]
    totals = np.add.outer(np.arange(n), np.arange(n))
    p_over = float(matrix[totals > line].sum())
    p_under = float(matrix[totals < line].sum())
    return {"over": p_over, "under": p_under}


def market_ou_all(matrix: np.ndarray) -> dict[str, dict[str, float]]:
    return {str(line): market_ou(matrix, line) for line in OU_LINES}


def top_correct_scores(matrix: np.ndarray, top_n: int = 3) -> list[dict]:
    n = matrix.shape[0]
    flat = [
        {"score": f"{g}-{h}", "p": float(matrix[g, h])}
        for g in range(n)
        for h in range(n)
    ]
    flat.sort(key=lambda item: item["p"], reverse=True)
    return flat[:top_n]


def confidence_level(market_1x2_probs: dict[str, float], lambda_home: float, lambda_away: float) -> str:
    """Regla del spec (seccion 9.7): la confianza sale del motor, no del LLM."""
    max_p = max(market_1x2_probs.values())
    lambda_diff = abs(lambda_home - lambda_away)
    if max_p >= 0.55 and lambda_diff >= 0.6:
        return "alta"
    if max_p < 0.40 or lambda_diff < 0.25:
        return "baja"
    return "media"
