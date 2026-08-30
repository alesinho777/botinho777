"""Configuracion del proyecto leida de variables de entorno (ver seccion 14 del spec)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    admin_telegram_id: str
    llm_provider: str
    llm_api_key: str
    llm_model: str
    database_path: str
    max_free_queries_per_day: int
    max_free_chat_questions: int
    timezone: str
    smtp_user: str
    smtp_app_password: str
    app_base_url: str
    football_data_api_key: str


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        admin_telegram_id=os.getenv("ADMIN_TELEGRAM_ID", ""),
        llm_provider=os.getenv("LLM_PROVIDER", "none"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        database_path=os.getenv("DATABASE_PATH", "data/botinho.db"),
        max_free_queries_per_day=int(os.getenv("MAX_FREE_QUERIES_PER_DAY", "5")),
        max_free_chat_questions=int(os.getenv("MAX_FREE_CHAT_QUESTIONS", "3")),
        timezone=os.getenv("TIMEZONE", "America/Asuncion"),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_app_password=os.getenv("SMTP_APP_PASSWORD", ""),
        app_base_url=os.getenv("APP_BASE_URL", "http://localhost:8501"),
        football_data_api_key=os.getenv("FOOTBALL_DATA_API_KEY", ""),
    )


# Parametros del motor (seccion 11 del spec).
MAX_GOALS = 8
CLAMP_LAMBDA_MIN = 0.20
CLAMP_LAMBDA_MAX = 4.00
SMOOTHING_K = 6  # regresion a la media para att/def con pocos partidos
DECAY_HALF_LIFE_DAYS = 180
DEFAULT_HOME_ADV = 1.25
RHO_BOUNDS = (-0.4, 0.4)  # rango seguro para el parametro Dixon-Coles (seccion 11.5)
