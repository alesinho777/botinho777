from dataclasses import dataclass

import pytest

from src.webapp.email import EmailNotConfiguredError, send_email


@dataclass
class _FakeSettings:
    smtp_user: str
    smtp_app_password: str


class _FakeSmtpClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.starttls_called = False
        self.login_calls: list[tuple] = []
        self.sent_messages: list = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def starttls(self):
        self.starttls_called = True

    def login(self, user, password):
        self.login_calls.append((user, password))

    def send_message(self, message):
        self.sent_messages.append(message)


def test_send_email_raises_when_not_configured():
    settings = _FakeSettings(smtp_user="", smtp_app_password="")
    with pytest.raises(EmailNotConfiguredError):
        send_email("alguien@test.com", "asunto", "cuerpo", settings=settings)


def test_send_email_uses_smtp_client_correctly():
    settings = _FakeSettings(smtp_user="bot@gmail.com", smtp_app_password="app-password-falsa")
    created_clients: list[_FakeSmtpClient] = []

    def factory(host, port):
        client = _FakeSmtpClient(host, port)
        created_clients.append(client)
        return client

    send_email(
        "usuario@test.com",
        "Tu código",
        "El código es 123456",
        settings=settings,
        smtp_client_factory=factory,
    )

    assert len(created_clients) == 1
    client = created_clients[0]
    assert client.host == "smtp.gmail.com"
    assert client.port == 587
    assert client.starttls_called is True
    assert client.login_calls == [("bot@gmail.com", "app-password-falsa")]
    assert len(client.sent_messages) == 1

    message = client.sent_messages[0]
    assert message["To"] == "usuario@test.com"
    assert message["Subject"] == "Tu código"
    assert "123456" in message.get_content()
