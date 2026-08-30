"""Habilitacion manual de premium (equivalente web del `/grant` de la seccion
16.7 del spec). Corre el dueño despues de recibir el pago por fuera.

Uso:
    python scripts/grant_premium.py --email alguien@mail.com --days 30
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, ".")

from src.config import load_settings  # noqa: E402
from src.webapp.auth import get_user  # noqa: E402
from src.webapp.db import get_connection  # noqa: E402


def grant_premium(email: str, days: int, database_path: str | None = None) -> str:
    if get_user(email, database_path) is None:
        raise ValueError(f"No existe ninguna cuenta registrada con {email}. Tiene que registrarse primero en la web.")

    tz = ZoneInfo(load_settings().timezone)
    premium_until = (datetime.now(tz).date() + timedelta(days=days)).isoformat()

    conn = get_connection(database_path)
    try:
        conn.execute(
            "UPDATE users SET role = 'premium', premium_until = ? WHERE email = ?",
            (premium_until, email),
        )
        conn.commit()
    finally:
        conn.close()
    return premium_until


def main() -> None:
    parser = argparse.ArgumentParser(description="Habilitar premium manualmente para un email")
    parser.add_argument("--email", required=True)
    parser.add_argument("--days", type=int, required=True)
    args = parser.parse_args()

    premium_until = grant_premium(args.email, args.days)
    print(f"{args.email} queda premium hasta {premium_until}.")


if __name__ == "__main__":
    main()
