"""Tope free diario y rol premium para la web (equivalente del `daily_count` /
`premium_until` de la seccion 7.5 del spec). Logica pura, sin Streamlit."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import load_settings
from src.webapp.db import get_connection


def current_date_str(timezone: str | None = None) -> str:
    tz = ZoneInfo(timezone or load_settings().timezone)
    return datetime.now(tz).date().isoformat()


def is_premium_active(user: dict) -> bool:
    if user.get("role") != "premium":
        return False
    premium_until = user.get("premium_until")
    if not premium_until:
        return False
    return premium_until >= current_date_str()


def _reset_if_new_day(user: dict, database_path: str | None = None) -> dict:
    today = current_date_str()
    if user.get("last_reset_date") == today:
        return user

    conn = get_connection(database_path)
    try:
        conn.execute(
            "UPDATE users SET daily_count = 0, chat_count = 0, last_reset_date = ? WHERE email = ?",
            (today, user["email"]),
        )
        conn.commit()
    finally:
        conn.close()

    updated = dict(user)
    updated["daily_count"] = 0
    updated["chat_count"] = 0
    updated["last_reset_date"] = today
    return updated


def can_query(user: dict, database_path: str | None = None) -> bool:
    if is_premium_active(user):
        return True
    user = _reset_if_new_day(user, database_path)
    return user["daily_count"] < load_settings().max_free_queries_per_day


def register_query(user: dict, database_path: str | None = None) -> None:
    if is_premium_active(user):
        return
    user = _reset_if_new_day(user, database_path)

    conn = get_connection(database_path)
    try:
        conn.execute("UPDATE users SET daily_count = daily_count + 1 WHERE email = ?", (user["email"],))
        conn.commit()
    finally:
        conn.close()


def can_ask_chat_question(user: dict, database_path: str | None = None) -> bool:
    if is_premium_active(user):
        return True
    user = _reset_if_new_day(user, database_path)
    return user["chat_count"] < load_settings().max_free_chat_questions


def register_chat_question(user: dict, database_path: str | None = None) -> None:
    if is_premium_active(user):
        return
    user = _reset_if_new_day(user, database_path)

    conn = get_connection(database_path)
    try:
        conn.execute("UPDATE users SET chat_count = chat_count + 1 WHERE email = ?", (user["email"],))
        conn.commit()
    finally:
        conn.close()
