from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


REQUIRED_LISTING_FIELDS = [
    "listing_id",
    "run_id",
    "trace_id",
    "sku",
    "market_id",
    "language",
    "title",
    "bullet_points",
    "description",
    "attributes",
    "claims",
    "retrieved_chunks",
    "prompt_version",
    "model_info",
    "status",
]


@dataclass(frozen=True)
class JsonParseResult:
    value: Optional[Dict[str, Any]]
    error: Optional[str] = None
    repaired: bool = False


def try_parse_json(raw_output: str) -> JsonParseResult:
    try:
        value = json.loads(raw_output)
        return JsonParseResult(value=value if isinstance(value, dict) else None)
    except json.JSONDecodeError as first_error:
        repaired = repair_common_json_errors(raw_output)
        try:
            value = json.loads(repaired)
            return JsonParseResult(value=value if isinstance(value, dict) else None, repaired=True)
        except json.JSONDecodeError:
            return JsonParseResult(value=None, error=str(first_error), repaired=False)


def repair_common_json_errors(raw_output: str) -> str:
    repaired = raw_output.strip()
    repaired = re.sub(r"'", '"', repaired)
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    return repaired


def validate_generated_listing_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field in REQUIRED_LISTING_FIELDS:
        if field not in payload:
            errors.append(f"missing field: {field}")
    if "bullet_points" in payload and not isinstance(payload["bullet_points"], list):
        errors.append("bullet_points must be a list")
    if "attributes" in payload and not isinstance(payload["attributes"], dict):
        errors.append("attributes must be an object")
    if "retrieved_chunks" in payload and not isinstance(payload["retrieved_chunks"], list):
        errors.append("retrieved_chunks must be a list")
    return errors
