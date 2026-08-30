import re

import pytest

from src.webapp.auth import (
    EmailAlreadyRegisteredError,
    InvalidResetCodeError,
    authenticate,
    get_user,
    register_user,
    request_password_reset,
    reset_password,
)
from src.webapp.db import get_connection


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_botinho.db")


def test_register_and_authenticate(db_path):
    register_user("user@test.com", "supersecreta", database_path=db_path)

    user = authenticate("user@test.com", "supersecreta", database_path=db_path)
    assert user is not None
    assert user["email"] == "user@test.com"
    assert user["role"] == "free"
    assert user["daily_count"] == 0


def test_authenticate_wrong_password_fails(db_path):
    register_user("user@test.com", "supersecreta", database_path=db_path)
    assert authenticate("user@test.com", "otra_password", database_path=db_path) is None


def test_authenticate_unknown_email_fails(db_path):
    assert authenticate("nadie@test.com", "loquesea", database_path=db_path) is None


def test_register_duplicate_email_raises(db_path):
    register_user("user@test.com", "supersecreta", database_path=db_path)
    with pytest.raises(EmailAlreadyRegisteredError):
        register_user("user@test.com", "otra_password", database_path=db_path)


def test_get_user_returns_none_when_missing(db_path):
    assert get_user("nadie@test.com", database_path=db_path) is None


def _capture_email(sent: list):
    def fake_send_email(to_email, subject, body):
        sent.append({"to_email": to_email, "subject": subject, "body": body})

    return fake_send_email


def _extract_token(body: str) -> str:
    match = re.search(r"reset_token=([\w\-]+)", body)
    assert match is not None
    return match.group(1)


def test_request_password_reset_sends_link_and_reset_password_works(db_path):
    register_user("user@test.com", "vieja_password", database_path=db_path)
    sent = []
    request_password_reset("user@test.com", database_path=db_path, send_email_fn=_capture_email(sent))

    assert len(sent) == 1
    assert sent[0]["to_email"] == "user@test.com"
    token = _extract_token(sent[0]["body"])

    reset_password("user@test.com", token, "nueva_password", database_path=db_path)

    assert authenticate("user@test.com", "nueva_password", database_path=db_path) is not None
    assert authenticate("user@test.com", "vieja_password", database_path=db_path) is None


def test_reset_password_wrong_token_raises(db_path):
    register_user("user@test.com", "vieja_password", database_path=db_path)
    sent = []
    request_password_reset("user@test.com", database_path=db_path, send_email_fn=_capture_email(sent))

    with pytest.raises(InvalidResetCodeError):
        reset_password("user@test.com", "un-token-invalido", "nueva_password", database_path=db_path)


def test_reset_password_expired_token_raises(db_path):
    register_user("user@test.com", "vieja_password", database_path=db_path)
    sent = []
    request_password_reset("user@test.com", database_path=db_path, send_email_fn=_capture_email(sent))
    token = _extract_token(sent[0]["body"])

    conn = get_connection(db_path)
    conn.execute(
        "UPDATE users SET reset_code_expires_at = ? WHERE email = ?",
        ("2000-01-01T00:00:00+00:00", "user@test.com"),
    )
    conn.commit()
    conn.close()

    with pytest.raises(InvalidResetCodeError):
        reset_password("user@test.com", token, "nueva_password", database_path=db_path)


def test_reset_token_is_single_use(db_path):
    register_user("user@test.com", "vieja_password", database_path=db_path)
    sent = []
    request_password_reset("user@test.com", database_path=db_path, send_email_fn=_capture_email(sent))
    token = _extract_token(sent[0]["body"])

    reset_password("user@test.com", token, "nueva_password", database_path=db_path)

    with pytest.raises(InvalidResetCodeError):
        reset_password("user@test.com", token, "otra_password_mas", database_path=db_path)


def test_request_password_reset_unknown_email_is_silent_noop(db_path):
    sent = []
    request_password_reset("nadie@test.com", database_path=db_path, send_email_fn=_capture_email(sent))
    assert sent == []
