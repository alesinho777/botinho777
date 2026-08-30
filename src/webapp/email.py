"""Envio de emails via Gmail SMTP (para el codigo de "olvide mi contrasena").

Eleccion deliberada de Gmail (no generico como el proveedor de LLM): el
usuario va a usar una cuenta de Gmail propia con una "contrasena de
aplicacion". Sin librerias nuevas: smtplib + email.message de la stdlib.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from src.config import load_settings

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


class EmailNotConfiguredError(Exception):
    pass


def send_email(
    to_email: str,
    subject: str,
    body: str,
    settings=None,
    smtp_client_factory=None,
) -> None:
    settings = settings or load_settings()
    if not settings.smtp_user or not settings.smtp_app_password:
        raise EmailNotConfiguredError(
            "Falta configurar el envio de emails (SMTP_USER y SMTP_APP_PASSWORD en .env)."
        )

    message = EmailMessage()
    message["From"] = settings.smtp_user
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    smtp_client_factory = smtp_client_factory or smtplib.SMTP
    with smtp_client_factory(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_app_password)
        server.send_message(message)
