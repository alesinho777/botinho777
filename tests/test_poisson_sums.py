from src.model.poisson import clamp_lambda, dixon_coles_tau, score_matrix


def test_matrix_sums_to_one():
    matrix = score_matrix(1.5, 1.1)
    assert abs(matrix.sum() - 1.0) < 1e-9


def test_matrix_sums_to_one_extreme_lambdas():
    for lh, la in [(0.2, 0.2), (4.0, 4.0), (0.2, 4.0), (2.7, 0.9)]:
        matrix = score_matrix(lh, la)
        assert abs(matrix.sum() - 1.0) < 1e-9


def test_clamp_lambda_respects_bounds():
    assert clamp_lambda(-1.0) == 0.20
    assert clamp_lambda(0.0) == 0.20
    assert clamp_lambda(10.0) == 4.00
    assert clamp_lambda(1.5) == 1.5


def test_matrix_shape_is_max_goals_plus_one():
    matrix = score_matrix(1.7, 1.2, max_goals=8)
    assert matrix.shape == (9, 9)


def test_matrix_with_rho_still_sums_to_one():
    for rho in (-0.3, -0.1, 0.1, 0.3):
        matrix = score_matrix(1.5, 1.1, rho=rho)
        assert abs(matrix.sum() - 1.0) < 1e-9


def test_rho_zero_matches_no_rho_argument():
    with_zero = score_matrix(1.5, 1.1, rho=0.0)
    without_arg = score_matrix(1.5, 1.1)
    assert (with_zero == without_arg).all()


def test_negative_rho_boosts_low_draws_and_shrinks_10_01():
    lh, la = 1.5, 1.1
    baseline = score_matrix(lh, la)
    corrected = score_matrix(lh, la, rho=-0.15)

    baseline_draws = baseline[0, 0] + baseline[1, 1]
    corrected_draws = corrected[0, 0] + corrected[1, 1]
    assert corrected_draws > baseline_draws

    baseline_10_01 = baseline[1, 0] + baseline[0, 1]
    corrected_10_01 = corrected[1, 0] + corrected[0, 1]
    assert corrected_10_01 < baseline_10_01


def test_dixon_coles_tau_is_one_outside_low_scores():
    assert dixon_coles_tau(2, 1, 1.5, 1.1, rho=-0.2) == 1.0
    assert dixon_coles_tau(3, 3, 1.5, 1.1, rho=-0.2) == 1.0
