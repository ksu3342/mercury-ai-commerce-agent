from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from app.llm.base import LLMProvider
from app.llm.types import LLMGenerationResult


class OpenAICompatibleProvider(LLMProvider):
    """Production adapter boundary; intentionally disabled in this MVP."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        enabled: bool = False,
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds

    def generate_listing_json(
        self,
        product: Any,
        market_config: Any,
        retrieved_chunks: Iterable[Any],
        prompt_version: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> LLMGenerationResult:
        raise NotImplementedError(
            "OpenAICompatibleProvider is a disabled production boundary skeleton. "
            "This MVP must not call external LLM services in tests or demo runs."
        )
