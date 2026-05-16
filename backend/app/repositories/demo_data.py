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


DEFAULT_SKU = "MRC-BLEND-450-WH"


class DemoDataRepository:
    """Loads lightweight demo cases and shared policy fixtures."""

    def __init__(self, demo_data_dir: Optional[Path] = None) -> None:
        project_root = Path(__file__).resolve().parents[3]
        self.project_root = project_root
        self.demo_data_dir = demo_data_dir or project_root / "data" / "demo"
        self.cases_dir = project_root / "data" / "cases"
        self.shared_dir = project_root / "data" / "shared"

    def _json_path(self, file_name: str, base_dir: Optional[Path] = None) -> Path:
        return (base_dir or self.demo_data_dir) / file_name

    def _read_json(self, file_name: str, base_dir: Optional[Path] = None) -> Any:
        path = self._json_path(file_name, base_dir)
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _read_jsonl(self, file_name: str, base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        path = self._json_path(file_name, base_dir)
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def get_product_by_sku(self, sku: str) -> ProductInput:
        return ProductInput.model_validate(self._read_json("product_input.json", self._case_dir_by_sku(sku)))

    def get_product_by_id(self, product_id: str) -> ProductInput:
        for case_dir in self._iter_case_dirs():
            product = ProductInput.model_validate(self._read_json("product_input.json", case_dir))
            if product.product_id == product_id:
                return product
        raise KeyError(f"Product ID not found: {product_id}")

    def get_market_configs(self) -> List[MarketConfig]:
        return [
            MarketConfig.model_validate(row)
            for row in self._read_json("market_configs.json", self._shared_or_demo_dir())
        ]

    def get_market_config(self, market_id: str) -> MarketConfig:
        for config in self.get_market_configs():
            if config.market_id == market_id:
                return config
        raise KeyError(f"Market config not found: {market_id}")

    def get_policy_rules(self) -> List[PolicyRule]:
        return [
            PolicyRule.model_validate(row)
            for row in self._read_jsonl("policy_rules.jsonl", self._shared_or_demo_dir())
        ]

    def get_rag_chunks(self) -> List[RagChunk]:
        return [
            RagChunk.model_validate(row)
            for row in self._read_jsonl("policy_chunks.jsonl", self._shared_or_demo_dir())
        ]

    def get_expected_listings(self, sku: Optional[str] = None) -> List[GeneratedListing]:
        case_dir = self._case_dir_by_sku(sku or DEFAULT_SKU)
        return [
            GeneratedListing.model_validate(row)
            for row in self._read_json("expected_generated_listings.json", case_dir)
        ]

    def get_expected_compliance_report(self, sku: Optional[str] = None) -> Dict[str, Any]:
        return self._read_json("expected_compliance_report.json", self._case_dir_by_sku(sku or DEFAULT_SKU))

    def get_expected_human_review(self, sku: Optional[str] = None) -> HumanReview:
        return HumanReview.model_validate(self._read_json("human_review.json", self._case_dir_by_sku(sku or DEFAULT_SKU)))

    def get_export_payload(self, sku: Optional[str] = None) -> Dict[str, Any]:
        return self._read_json("shopify_like_payload.json", self._case_dir_by_sku(sku or DEFAULT_SKU))

    def list_demo_cases(self) -> List[ProductInput]:
        return [
            ProductInput.model_validate(self._read_json("product_input.json", case_dir))
            for case_dir in self._iter_case_dirs()
        ]

    def _case_dir_by_sku(self, sku: str) -> Path:
        for case_dir in self._iter_case_dirs():
            product = ProductInput.model_validate(self._read_json("product_input.json", case_dir))
            if product.sku == sku:
                return case_dir
        raise KeyError(f"Product SKU not found: {sku}")

    def _iter_case_dirs(self) -> List[Path]:
        case_dirs: List[Path] = []
        if self.cases_dir.exists():
            case_dirs.extend(
                sorted(
                    path
                    for path in self.cases_dir.iterdir()
                    if path.is_dir() and (path / "product_input.json").exists()
                )
            )
        if (self.demo_data_dir / "product_input.json").exists():
            case_dirs.append(self.demo_data_dir)
        return case_dirs

    def _shared_or_demo_dir(self) -> Path:
        if (self.shared_dir / "market_configs.json").exists():
            return self.shared_dir
        return self.demo_data_dir
