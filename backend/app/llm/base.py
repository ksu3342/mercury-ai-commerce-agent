from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional

from app.llm.types import LLMGenerationResult


class LLMProvider(ABC):
    @abstractmethod
    def generate_listing_json(
        self,
        product: Any,
        market_config: Any,
        retrieved_chunks: Iterable[Any],
        prompt_version: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> LLMGenerationResult:
        """Return one structured listing payload for a product and market."""
