from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas import (
    GeneratedListing,
    HumanReview,
    MarketConfig,
    PolicyRule,
    ProductInput,
    RagChunk,
)


class DemoDataRepository:
    """Loads the fixed Portfolio PoC data set from data/demo."""

    def __init__(self, demo_data_dir: Optional[Path] = None) -> None:
        project_root = Path(__file__).resolve().parents[3]
        self.demo_data_dir = demo_data_dir or project_root / "data" / "demo"

    def _json_path(self, file_name: str) -> Path:
        return self.demo_data_dir / file_name

    def _read_json(self, file_name: str) -> Any:
        path = self._json_path(file_name)
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _read_jsonl(self, file_name: str) -> List[Dict[str, Any]]:
        path = self._json_path(file_name)
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def get_product_by_sku(self, sku: str) -> ProductInput:
        product = ProductInput.model_validate(self._read_json("product_input.json"))
        if product.sku != sku:
            raise KeyError(f"Product SKU not found: {sku}")
        return product

    def get_product_by_id(self, product_id: str) -> ProductInput:
        product = ProductInput.model_validate(self._read_json("product_input.json"))
        if product.product_id != product_id:
            raise KeyError(f"Product ID not found: {product_id}")
        return product

    def get_market_configs(self) -> List[MarketConfig]:
        return [MarketConfig.model_validate(row) for row in self._read_json("market_configs.json")]

    def get_market_config(self, market_id: str) -> MarketConfig:
        for config in self.get_market_configs():
            if config.market_id == market_id:
                return config
        raise KeyError(f"Market config not found: {market_id}")

    def get_policy_rules(self) -> List[PolicyRule]:
        return [PolicyRule.model_validate(row) for row in self._read_jsonl("policy_rules.jsonl")]

    def get_rag_chunks(self) -> List[RagChunk]:
        return [RagChunk.model_validate(row) for row in self._read_jsonl("policy_chunks.jsonl")]

    def get_expected_listings(self) -> List[GeneratedListing]:
        return [
            GeneratedListing.model_validate(row)
            for row in self._read_json("expected_generated_listings.json")
        ]

    def get_expected_compliance_report(self) -> Dict[str, Any]:
        return self._read_json("expected_compliance_report.json")

    def get_expected_human_review(self) -> HumanReview:
        return HumanReview.model_validate(self._read_json("human_review.json"))

    def get_export_payload(self) -> Dict[str, Any]:
        return self._read_json("shopify_like_payload.json")
