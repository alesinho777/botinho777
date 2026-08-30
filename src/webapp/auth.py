"""Registro/login por email+password para la demo web (sin libreria externa
de auth: hashing con hashlib, stdlib). Logica pura, sin Streamlit, para
poder testear con pytest."""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from src.config import load_settings
from src.webapp.db import get_connection
from src.webapp.email import send_email

PBKDF2_ITERATIONS = 200_000
RESET_CODE_TTL_MINUTES = 15


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidResetCodeError(Exception):
    pass


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, password_hash_hex: str) -> bool:
    _, digest_hex = hash_password(password, bytes.fromhex(salt_hex))
    return digest_hex == password_hash_hex


def get_user(email: str, database_path: str | None = None) -> dict | None:
    conn = get_connection(database_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def register_user(email: str, password: str, database_path: str | None = None) -> None:
    if get_user(email, database_path) is not None:
        raise EmailAlreadyRegisteredError(f"Ya hay una cuenta registrada con {email}")

    salt_hex, password_hash_hex = hash_password(password)
    conn = get_connection(database_path)
    try:
        conn.execute(
            "INSERT INTO users (email, salt_hex, password_hash_hex) VALUES (?, ?, ?)",
            (email, salt_hex, password_hash_hex),
        )
        conn.commit()
    finally:
        conn.close()


def authenticate(email: str, password: str, database_path: str | None = None) -> dict | None:
    user = get_user(email, database_path)
    if user is None:
        return None
    if not verify_password(password, user["salt_hex"], user["password_hash_hex"]):
        return None
    return user


def request_password_reset(
    email: str, database_path: str | None = None, send_email_fn=None, base_url: str | None = None
) -> None:
    """Genera un token de un solo uso y manda un link de reseteo por email. Si
    el email no esta registrado, no hace nada (no revela que emails existen)."""
    send_email_fn = send_email_fn or send_email
    base_url = base_url or load_settings().app_base_url

    user = get_user(email, database_path)
    if user is None:
        return

    token = secrets.token_urlsafe(32)
    salt_hex, token_hash_hex = hash_password(token)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_TTL_MINUTES)).isoformat()

    conn = get_connection(database_path)
    try:
        conn.execute(
            "UPDATE users SET reset_code_salt_hex = ?, reset_code_hash_hex = ?, "
            "reset_code_expires_at = ? WHERE email = ?",
            (salt_hex, token_hash_hex, expires_at, email),
        )
        conn.commit()
    finally:
        conn.close()

    query = urlencode({"reset_email": email, "reset_token": token})
    reset_link = f"{base_url}?{query}"

    send_email_fn(
        to_email=email,
        subject="Restablecé tu contraseña en Botinho777",
        body=(
            f"Entrá a este link para poner una contraseña nueva en Botinho777:\n\n{reset_link}\n\n"
            f"Vence en {RESET_CODE_TTL_MINUTES} minutos. Si no pediste esto, ignorá este mensaje."
        ),
    )


def reset_password(
    email: str, token: str, new_password: str, database_path: str | None = None
) -> None:
    user = get_user(email, database_path)
    if user is None or not user.get("reset_code_hash_hex"):
        raise InvalidResetCodeError("Link inválido o vencido.")

    expires_at = user.get("reset_code_expires_at")
    if not expires_at or datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
        raise InvalidResetCodeError("Link inválido o vencido.")

    if not verify_password(token, user["reset_code_salt_hex"], user["reset_code_hash_hex"]):
        raise InvalidResetCodeError("Link inválido o vencido.")

    salt_hex, password_hash_hex = hash_password(new_password)
    conn = get_connection(database_path)
    try:
        conn.execute(
            "UPDATE users SET salt_hex = ?, password_hash_hex = ?, "
            "reset_code_salt_hex = NULL, reset_code_hash_hex = NULL, reset_code_expires_at = NULL "
            "WHERE email = ?",
            (salt_hex, password_hash_hex, email),
        )
        conn.commit()
    finally:
        conn.close()
