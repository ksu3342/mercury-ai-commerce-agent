from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ImageAsset(StrictBaseModel):
    url: str
    alt_text: Optional[str] = None
    ocr_text: Optional[str] = None


class ProductInput(StrictBaseModel):
    product_id: Optional[str] = None
    sku: str
    source_language: str
    title: str
    description: Optional[str] = None
    brand: Optional[str] = None
    category_hint: str
    target_markets: List[str]
    target_languages: List[str]
    attributes: Dict[str, Any] = Field(default_factory=dict)
    image_assets: List[ImageAsset] = Field(default_factory=list)
    regulatory_tags: List[str] = Field(default_factory=list)
    source_metadata: Optional[Dict[str, Any]] = None

    @field_validator("sku", "source_language", "title", "category_hint")
    @classmethod
    def non_empty_string(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value

    @field_validator("target_markets", "target_languages")
    @classmethod
    def non_empty_list(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("must not be empty")
        return value


class MarketConfig(StrictBaseModel):
    market_id: str
    region: str
    country_code: str
    language: str
    currency: str
    unit_system: Literal["metric", "imperial"]
    platform: str
    required_attributes: List[str]
    forbidden_claims: List[str] = Field(default_factory=list)
    locale_rules: Dict[str, Any] = Field(default_factory=dict)
    compliance_profile: Dict[str, Any]
    export_profile: Dict[str, Any]


class PolicyRule(StrictBaseModel):
    rule_id: str
    version: str
    market_ids: List[str]
    category_scope: List[str] = Field(default_factory=list)
    rule_type: str
    severity: Literal["blocker", "warning", "info"]
    source: Dict[str, Any]
    condition: Dict[str, Any]
    check: Dict[str, Any]
    message: str
    remediation: str
    examples: List[Dict[str, Any]] = Field(default_factory=list)


class RagChunk(StrictBaseModel):
    chunk_id: str
    rule_id: Optional[str] = None
    policy_version: str = Field(alias="version")
    source_type: str
    market_ids: List[str]
    languages: List[str] = Field(default_factory=list)
    category_scope: List[str] = Field(default_factory=list)
    risk_tags: List[str] = Field(default_factory=list)
    severity: Optional[str] = None
    text: str
    score: float = 0.0


class RetrievedChunkRef(StrictBaseModel):
    chunk_id: str
    rule_id: Optional[str] = None
    source: Optional[str] = None
    policy_version: Optional[str] = None
    score: Optional[float] = None
    text: Optional[str] = None


class ListingClaim(StrictBaseModel):
    claim_id: str
    text: str
    claim_type: str
    source_attribute: Optional[str] = None


class GeneratedListing(StrictBaseModel):
    listing_id: str
    run_id: str
    trace_id: str
    sku: str
    market_id: str
    language: str
    title: str
    bullet_points: List[str]
    description: str
    seo_keywords: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any]
    claims: List[ListingClaim] = Field(default_factory=list)
    retrieved_chunks: List[RetrievedChunkRef]
    prompt_version: str
    model_info: Dict[str, Any]
    export_payloads: Optional[Dict[str, Any]] = None
    status: str

    @field_validator("bullet_points")
    @classmethod
    def bullets_not_empty(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("bullet_points must not be empty")
        return value


class ComplianceIssue(StrictBaseModel):
    issue_id: str = Field(alias="check_id")
    rule_id: str
    status: Literal["passed", "warning", "failed"]
    severity: Literal["blocker", "warning", "info"]
    message: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    suggestion: Optional[str] = Field(default=None, alias="suggested_fix")


class ComplianceReport(StrictBaseModel):
    report_id: str
    run_id: str
    trace_id: str
    listing_id: str
    market_id: str
    overall_status: Literal["pass", "warning", "blocker"]
    score: float
    checks: List[ComplianceIssue]
    validator_result: Dict[str, Any]
    retrieved_chunks: List[RetrievedChunkRef]
    policy_version: str
    created_at: str = Field(default_factory=utc_now_iso)


class HumanReview(StrictBaseModel):
    review_id: str
    run_id: str
    trace_id: str
    listing_id: str
    reviewer_id: str
    decision: Literal["approved", "changes_requested", "rejected"]
    edited_listing: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None
    edit_summary: Dict[str, Any]
    human_review_result: Dict[str, Any]
    reviewed_at: str


class TraceEvent(StrictBaseModel):
    node_name: str
    input_summary: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["success", "failed"]
    started_at: str
    finished_at: str
    error: Optional[str] = None


class RunTrace(StrictBaseModel):
    run_id: str
    trace_id: str
    events: List[TraceEvent]


class RunSummary(StrictBaseModel):
    run_id: str
    trace_id: str
    status: str
    current_state: str
    product_input: ProductInput
    retrieved_chunks: List[RagChunk]
    generated_listing: List[GeneratedListing]
    compliance_report: List[ComplianceReport]
    human_review: Optional[HumanReview] = None
    export_payload: Dict[str, Any] = Field(default_factory=dict)
    trace_events: List[TraceEvent] = Field(default_factory=list)
    observability: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class DemoRunRequest(StrictBaseModel):
    sku: str
    target_markets: List[str]
    target_languages: List[str]

    @field_validator("sku")
    @classmethod
    def sku_required(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("sku must not be empty")
        return value

    @field_validator("target_markets", "target_languages")
    @classmethod
    def targets_required(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("target list must not be empty")
        return value


class ReviewSubmitRequest(StrictBaseModel):
    run_id: str
    trace_id: Optional[str] = None
    listing_id: str
    reviewer_id: str
    decision: Literal["approved", "changes_requested", "rejected"]
    review_id: Optional[str] = None
    edited_listing: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None
    edit_summary: Optional[Dict[str, Any]] = None
    human_review_result: Dict[str, Any] = Field(default_factory=dict)
    reviewed_at: Optional[str] = None
