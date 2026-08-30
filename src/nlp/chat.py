"""Modo B — LLM narrator (seccion 12 del spec): el LLM NUNCA calcula
probabilidades, solo responde preguntas sobre el JSON que ya armo el motor.

El proveedor sale de las variables genericas de la seccion 14
(LLM_PROVIDER, LLM_API_KEY, LLM_MODEL), nunca hardcodeado."""
from __future__ import annotations

import json
import os

from src.config import load_settings

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
with open(_PROMPT_PATH, "r", encoding="utf-8") as _f:
    SYSTEM_PROMPT = _f.read().strip()

DEFAULT_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 500


class LlmNotConfiguredError(Exception):
    pass


def build_user_message(prediction: dict, question: str) -> str:
    """User prompt = JSON del partido + pregunta original (seccion 12 del spec)."""
    prediction_json = json.dumps(prediction, ensure_ascii=False)
    return (
        f"JSON del partido (unica fuente de datos permitida):\n{prediction_json}\n\n"
        f"Pregunta: {question}"
    )


def ask_llm(
    prediction: dict,
    question: str,
    history: list[dict[str, str]] | None = None,
    client=None,
    settings=None,
) -> str:
    settings = settings or load_settings()
    if settings.llm_provider != "anthropic" or not settings.llm_api_key:
        raise LlmNotConfiguredError(
            "Falta configurar el LLM (LLM_PROVIDER=anthropic y LLM_API_KEY en .env)."
        )

    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.llm_api_key)

    messages = list(history or [])
    messages.append({"role": "user", "content": build_user_message(prediction, question)})

    response = client.messages.create(
        model=settings.llm_model or DEFAULT_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text
