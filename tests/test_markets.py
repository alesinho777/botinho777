from src.model.markets import (
    confidence_level,
    market_1x2,
    market_btts,
    market_ou_all,
    top_correct_scores,
)
from src.model.poisson import score_matrix


def test_markets_are_consistent_and_sum_to_one():
    matrix = score_matrix(1.72, 1.18)

    probs_1x2 = market_1x2(matrix)
    assert abs(sum(probs_1x2.values()) - 1.0) < 1e-9

    probs_btts = market_btts(matrix)
    assert abs(sum(probs_btts.values()) - 1.0) < 1e-9

    for line, probs in market_ou_all(matrix).items():
        assert abs(sum(probs.values()) - 1.0) < 1e-9

    top = top_correct_scores(matrix, top_n=3)
    assert len(top) == 3
    assert sum(item["p"] for item in top) < 1.0


def test_example_river_boca():
    """Ejemplo trabajado de la seccion 11.8 del spec (lambdas fijos de calibracion)."""
    lambda_home = 2.10
    lambda_away = 1.09

    matrix = score_matrix(lambda_home, lambda_away)
    probs_1x2 = market_1x2(matrix)

    assert probs_1x2["H"] > probs_1x2["A"]
    assert abs(sum(probs_1x2.values()) - 1.0) < 1e-9

    ou = market_ou_all(matrix)
    assert ou["2.5"]["over"] > 0.50

    top = top_correct_scores(matrix, top_n=1)
    assert top[0]["score"] in {"2-1", "1-1", "2-0", "3-1", "1-0"}


def test_confidence_level_thresholds():
    assert confidence_level({"H": 0.60, "D": 0.20, "A": 0.20}, lambda_home=2.0, lambda_away=1.0) == "alta"
    assert confidence_level({"H": 0.35, "D": 0.33, "A": 0.32}, lambda_home=1.5, lambda_away=1.4) == "baja"
    assert confidence_level({"H": 0.45, "D": 0.30, "A": 0.25}, lambda_home=1.6, lambda_away=1.2) == "media"
