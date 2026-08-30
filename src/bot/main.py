"""Entry point del bot de Telegram, modo polling (seccion 16.6 del spec).

El token SOLO sale de la variable de entorno TELEGRAM_BOT_TOKEN (.env). Nunca
hardcodear. Correr con: python -m src.bot.main
"""
from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from src.bot.handlers import historial, on_button, start
from src.config import load_settings


def build_application() -> Application:
    settings = load_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "Falta TELEGRAM_BOT_TOKEN. Copiá .env.example a .env y completá el token del bot."
        )

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("historial", historial))
    application.add_handler(CallbackQueryHandler(on_button))
    return application


def main() -> None:
    application = build_application()
    application.run_polling()


if __name__ == "__main__":
    main()
