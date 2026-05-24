"""Wrapper Anthropic — chamada com tool_use forçado contra o schema do relatório.

Usa prompt caching no system prompt (que é estável) e em blocos pesados do
contexto, pra acelerar gerações múltiplas (várias áreas no mesmo ciclo).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMConfig:
    model: str = "claude-opus-4-7"
    max_tokens: int = 16000


def get_client():
    """Inicializa o cliente Anthropic. Lê ANTHROPIC_API_KEY do ambiente."""
    from anthropic import Anthropic
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY não encontrada. Copie .env.example para .env "
            "e preencha a chave."
        )
    return Anthropic(api_key=api_key)


def generate_relatorio_payload(
    system_prompt: str,
    user_prompt: str,
    *,
    cfg: LLMConfig | None = None,
) -> dict[str, Any]:
    """Chama o Claude com tool_use forçado pelo `RELATORIO_TOOL_SCHEMA`."""
    from .template import RELATORIO_TOOL_SCHEMA

    cfg = cfg or LLMConfig()
    model = os.environ.get("RELINT_MODEL", cfg.model)
    client = get_client()

    msg = client.messages.create(
        model=model,
        max_tokens=cfg.max_tokens,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_prompt}],
        tools=[RELATORIO_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": RELATORIO_TOOL_SCHEMA["name"]},
    )

    for block in msg.content:
        if getattr(block, "type", None) == "tool_use":
            return block.input  # type: ignore[return-value]

    raise RuntimeError(
        "Claude não devolveu um bloco tool_use — resposta inesperada."
    )
