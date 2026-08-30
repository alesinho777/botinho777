from dataclasses import dataclass

import pytest

from src.nlp.chat import SYSTEM_PROMPT, LlmNotConfiguredError, ask_llm, build_user_message


@dataclass
class _FakeSettings:
    llm_provider: str
    llm_api_key: str
    llm_model: str = ""


class _FakeContentBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeResponse:
    def __init__(self, text: str):
        self.content = [_FakeContentBlock(text)]


class _FakeMessages:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self.response_text)


class _FakeClient:
    def __init__(self, response_text: str = "respuesta de prueba"):
        self.messages = _FakeMessages(response_text)


def _fake_prediction() -> dict:
    return {
        "fixture_id": "demo_2026-01-01_team_a_team_b",
        "home": "team_a",
        "away": "team_b",
        "markets": {"1x2": {"H": 0.5, "D": 0.3, "A": 0.2}},
        "confidence": "media",
    }


def test_ask_llm_raises_when_provider_not_anthropic():
    settings = _FakeSettings(llm_provider="none", llm_api_key="")
    with pytest.raises(LlmNotConfiguredError):
        ask_llm(_fake_prediction(), "¿por qué?", settings=settings)


def test_ask_llm_raises_when_missing_api_key():
    settings = _FakeSettings(llm_provider="anthropic", llm_api_key="")
    with pytest.raises(LlmNotConfiguredError):
        ask_llm(_fake_prediction(), "¿por qué?", settings=settings)


def test_ask_llm_uses_system_prompt_and_prediction_json():
    settings = _FakeSettings(llm_provider="anthropic", llm_api_key="fake-key", llm_model="modelo-de-prueba")
    client = _FakeClient(response_text="El local es favorito porque tiene mejor ataque.")

    result = ask_llm(_fake_prediction(), "¿por qué el local es favorito?", client=client, settings=settings)

    assert result == "El local es favorito porque tiene mejor ataque."
    assert len(client.messages.calls) == 1

    call = client.messages.calls[0]
    assert call["system"] == SYSTEM_PROMPT
    assert call["model"] == "modelo-de-prueba"
    user_message = call["messages"][-1]["content"]
    assert "demo_2026-01-01_team_a_team_b" in user_message
    assert "¿por qué el local es favorito?" in user_message


def test_build_user_message_includes_question_and_json():
    message = build_user_message(_fake_prediction(), "¿está muy parejo?")
    assert "¿está muy parejo?" in message
    assert '"home": "team_a"' in message
