"""Conexion sqlite para usuarios de la web (reemplaza, para el canal web, la
tabla `users` de la seccion 7.5 del spec: email en vez de telegram_id)."""
from __future__ import annotations

import os
import sqlite3

from src.config import load_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    salt_hex TEXT NOT NULL,
    password_hash_hex TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'free',
    premium_until TEXT,
    daily_count INTEGER NOT NULL DEFAULT 0,
    chat_count INTEGER NOT NULL DEFAULT 0,
    last_reset_date TEXT,
    reset_code_salt_hex TEXT,
    reset_code_hash_hex TEXT,
    reset_code_expires_at TEXT
);
"""

_NEW_COLUMNS = {
    "chat_count": "INTEGER NOT NULL DEFAULT 0",
    "reset_code_salt_hex": "TEXT",
    "reset_code_hash_hex": "TEXT",
    "reset_code_expires_at": "TEXT",
}


def _migrate(conn: sqlite3.Connection) -> None:
    """Migracion liviana: agrega columnas nuevas a bases creadas antes de que
    existieran (ej. chat_count para el limite del chat, reset_code_* para
    'olvide mi contrasena')."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    for name, ddl in _NEW_COLUMNS.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {name} {ddl}")
    conn.commit()


def get_connection(database_path: str | None = None) -> sqlite3.Connection:
    path = database_path or load_settings().database_path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    _migrate(conn)
    return conn
