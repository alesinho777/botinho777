import pytest

from src.webapp.auth import get_user, register_user
from src.webapp.db import get_connection
from src.webapp.quota import (
    can_ask_chat_question,
    can_query,
    current_date_str,
    is_premium_active,
    register_chat_question,
    register_query,
)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_botinho.db")


def _make_user(db_path, email="user@test.com") -> dict:
    register_user(email, "supersecreta", database_path=db_path)
    return get_user(email, database_path=db_path)


def _set_row(db_path, email, **fields) -> None:
    conn = get_connection(db_path)
    try:
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(f"UPDATE users SET {set_clause} WHERE email = ?", (*fields.values(), email))
        conn.commit()
    finally:
        conn.close()


def test_free_user_under_limit_can_query(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_QUERIES_PER_DAY", "3")
    user = _make_user(db_path)
    assert can_query(user, database_path=db_path) is True


def test_free_user_at_limit_is_blocked(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_QUERIES_PER_DAY", "3")
    user = _make_user(db_path)
    today = current_date_str()
    _set_row(db_path, user["email"], daily_count=3, last_reset_date=today)

    user = get_user(user["email"], database_path=db_path)
    assert can_query(user, database_path=db_path) is False


def test_register_query_increments_until_blocked(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_QUERIES_PER_DAY", "2")
    user = _make_user(db_path)

    for _ in range(2):
        user = get_user(user["email"], database_path=db_path)
        assert can_query(user, database_path=db_path) is True
        register_query(user, database_path=db_path)

    user = get_user(user["email"], database_path=db_path)
    assert can_query(user, database_path=db_path) is False


def test_daily_count_resets_on_new_day(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_QUERIES_PER_DAY", "3")
    user = _make_user(db_path)
    _set_row(db_path, user["email"], daily_count=99, last_reset_date="2000-01-01")

    user = get_user(user["email"], database_path=db_path)
    assert can_query(user, database_path=db_path) is True

    refreshed = get_user(user["email"], database_path=db_path)
    assert refreshed["daily_count"] == 0
    assert refreshed["last_reset_date"] == current_date_str()


def test_premium_active_ignores_daily_limit(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_QUERIES_PER_DAY", "1")
    user = _make_user(db_path)
    _set_row(db_path, user["email"], role="premium", premium_until="2999-01-01", daily_count=50)

    user = get_user(user["email"], database_path=db_path)
    assert is_premium_active(user) is True
    assert can_query(user, database_path=db_path) is True

    register_query(user, database_path=db_path)
    refreshed = get_user(user["email"], database_path=db_path)
    assert refreshed["daily_count"] == 50  # no se toca mientras es premium activo


def test_expired_premium_is_treated_as_free(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_QUERIES_PER_DAY", "1")
    user = _make_user(db_path)
    _set_row(db_path, user["email"], role="premium", premium_until="2000-01-01")

    user = get_user(user["email"], database_path=db_path)
    assert is_premium_active(user) is False


def test_free_user_under_chat_limit_can_ask(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_CHAT_QUESTIONS", "3")
    user = _make_user(db_path)
    assert can_ask_chat_question(user, database_path=db_path) is True


def test_register_chat_question_increments_until_blocked(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_CHAT_QUESTIONS", "3")
    user = _make_user(db_path)

    for _ in range(3):
        user = get_user(user["email"], database_path=db_path)
        assert can_ask_chat_question(user, database_path=db_path) is True
        register_chat_question(user, database_path=db_path)

    user = get_user(user["email"], database_path=db_path)
    assert can_ask_chat_question(user, database_path=db_path) is False


def test_chat_count_resets_on_new_day(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_CHAT_QUESTIONS", "3")
    user = _make_user(db_path)
    _set_row(db_path, user["email"], chat_count=99, last_reset_date="2000-01-01")

    user = get_user(user["email"], database_path=db_path)
    assert can_ask_chat_question(user, database_path=db_path) is True

    refreshed = get_user(user["email"], database_path=db_path)
    assert refreshed["chat_count"] == 0


def test_premium_active_ignores_chat_limit(db_path, monkeypatch):
    monkeypatch.setenv("MAX_FREE_CHAT_QUESTIONS", "1")
    user = _make_user(db_path)
    _set_row(db_path, user["email"], role="premium", premium_until="2999-01-01", chat_count=50)

    user = get_user(user["email"], database_path=db_path)
    assert can_ask_chat_question(user, database_path=db_path) is True

    register_chat_question(user, database_path=db_path)
    refreshed = get_user(user["email"], database_path=db_path)
    assert refreshed["chat_count"] == 50  # no se toca mientras es premium activo
