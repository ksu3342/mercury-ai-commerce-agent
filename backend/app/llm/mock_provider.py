from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional

from app.llm.base import LLMProvider
from app.llm.json_repair import validate_generated_listing_payload
from app.llm.types import LLMGenerationResult
from app.repositories import DemoDataRepository


DEFAULT_PROMPT_VERSION = "listing_generator_v1.1.0"
MOCK_MODEL_INFO = {
    "provider": "mock_llm",
    "model_name": "expected-listing-fixture",
    "temperature": 0.0,
}


class MockLLMProvider(LLMProvider):
    """Stable LLM boundary backed by expected listing fixtures."""

    def __init__(
        self,
        repository: DemoDataRepository,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ) -> None:
        self.repository = repository
        self.prompt_version = prompt_version

    def generate_listing_json(
        self,
        product: Any,
        market_config: Any,
        retrieved_chunks: Iterable[Any],
        prompt_version: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> LLMGenerationResult:
        payload = self._fixture_payload(product, market_config)
        payload["prompt_version"] = prompt_version
        payload["model_info"] = dict(MOCK_MODEL_INFO)
        return LLMGenerationResult(
            payload=payload,
            model_info=dict(MOCK_MODEL_INFO),
            prompt_version=prompt_version,
            raw_output=json.dumps(payload, ensure_ascii=True),
            validation_errors=validate_generated_listing_payload(payload),
        )

    def _fixture_payload(self, product: Any, market_config: Any) -> Dict[str, Any]:
        market_id = market_config.market_id
        for listing in self.repository.get_expected_listings(product.sku):
            if listing.market_id == market_id:
                return listing.model_dump()
        return self._fallback_payload(product, market_config)

    def _fallback_payload(self, product: Any, market_config: Any) -> Dict[str, Any]:
        attributes = dict(product.attributes)
        missing_fields = [
            field for field in market_config.required_attributes if attributes.get(field) in (None, "")
        ]
        for field in missing_fields:
            attributes.setdefault(field, None)
        if missing_fields:
            attributes["missing_fields"] = missing_fields
        return {
            "listing_id": f"lst_{product.sku.lower().replace('-', '_')}_{market_config.market_id.lower()}",
            "run_id": "run_pending",
            "trace_id": "trc_pending",
            "sku": product.sku,
            "market_id": market_config.market_id,
            "language": market_config.language,
            "title": f"{product.brand or 'Unknown'} {product.title}",
            "bullet_points": [
                "Draft created only from provided product attributes.",
                "Missing required fields are kept as null instead of being invented.",
            ],
            "description": product.description or "No source description provided.",
            "seo_keywords": [],
            "attributes": attributes,
            "claims": [],
            "retrieved_chunks": [],
            "prompt_version": self.prompt_version,
            "model_info": dict(MOCK_MODEL_INFO),
            "status": "draft",
        }
