"""60db LLM integration helper.

Hitchcock uses `smolagents.LiteLLMModel` for the script writer's LLM,
and `litellm.OpenAI` for character-description prompts in the DOP. Both
paths route through liteLLM under the hood, which supports any
OpenAI-compatible endpoint via `api_base` + `api_key`.

This module is the single place that injects 60db config so the rest of
the codebase just calls `get_litellm_model("o1")` and gets back either
a vanilla model or a 60db-routed one depending on `LLM_PROVIDER` env.

Reference: https://docs.60db.ai/api-reference/llm/chat-completion
"""

from __future__ import annotations

import os
from typing import Any

from smolagents import LiteLLMModel

DEFAULT_API_BASE = "https://api.60db.ai/v1"
DEFAULT_MODEL = "60db-tiny"


def is_sixtydb_active() -> bool:
    """True when the user opted into 60db for LLM routing."""
    return os.getenv("LLM_PROVIDER", "").strip().lower() in ("60db", "sixtydb")


def get_litellm_model(model_id: str, **kwargs: Any) -> LiteLLMModel:
    """Build a `LiteLLMModel`, routing to 60db when LLM_PROVIDER=sixtydb.

    Callers pass their original `model_id` (e.g. "o1"); when 60db is
    active, we override with SIXTYDB_LLM_MODEL (or `60db-tiny` default)
    and inject `api_base` + `api_key` so litellm hits the 60db endpoint.

    Any extra kwargs the caller would normally pass to `LiteLLMModel`
    (temperature, max_completion_tokens, custom_role_conversions, etc.)
    pass through unchanged.
    """
    if not is_sixtydb_active():
        return LiteLLMModel(model_id, **kwargs)

    api_key = os.getenv("SIXTYDB_API_KEY")
    if not api_key:
        # Match the existing fail-loud pattern from eleven_labs_service.
        raise ValueError(
            "LLM_PROVIDER=sixtydb but SIXTYDB_API_KEY is not set"
        )
    sixtydb_model = os.getenv("SIXTYDB_LLM_MODEL", DEFAULT_MODEL)
    api_base = os.getenv("SIXTYDB_API_BASE", "https://api.60db.ai").rstrip("/")
    if not api_base.endswith("/v1"):
        api_base = api_base + "/v1"

    # litellm routes any "openai/<model>" id through its OpenAI-compatible
    # path with the supplied api_base + api_key — exactly what 60db needs.
    return LiteLLMModel(
        f"openai/{sixtydb_model}",
        api_base=api_base,
        api_key=api_key,
        **kwargs,
    )
