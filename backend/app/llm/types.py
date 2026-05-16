from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LLMGenerationResult:
    payload: Dict[str, Any]
    model_info: Dict[str, Any]
    prompt_version: str
    raw_output: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
