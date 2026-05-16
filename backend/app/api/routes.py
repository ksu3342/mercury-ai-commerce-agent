from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.generators import MockListingGenerator
from app.observability import TraceRecorder
from app.repositories import DemoDataRepository, InMemoryRunStore
from app.retrievers import MockPolicyRetriever
from app.schemas import DemoRunRequest, HumanReview, ReviewSubmitRequest, utc_now_iso
from app.validators import RuleEngine
from app.workflow import DemoWorkflow


router = APIRouter()
SUPPORTED_MARKET_LANGUAGES = {"US": "en-US", "DE": "de-DE"}

repository = DemoDataRepository()
run_store = InMemoryRunStore()
retriever = MockPolicyRetriever(repository)
generator = MockListingGenerator(repository)
rule_engine = RuleEngine(repository.get_policy_rules(), repository.get_market_configs())
workflow = DemoWorkflow(repository, run_store, retriever, generator, rule_engine)


@router.post("/runs/demo")
def create_demo_run(request: DemoRunRequest) -> Dict[str, Any]:
    _validate_demo_scope(request)
    try:
        run = workflow.run(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "run_id": run.run_id,
        "trace_id": run.trace_id,
        "status": run.status,
        "generated_listing_summary": {
            "listing_count": len(run.generated_listing),
            "markets": [listing.market_id for listing in run.generated_listing],
            "languages": [listing.language for listing in run.generated_listing],
        },
        "compliance_summary": _compliance_summary(run.compliance_report),
        "links": {"run_detail": f"/runs/{run.run_id}"},
        "next_actions": ["submit_review", "fix_blockers"]
        if run.status == "review_required"
        else ["submit_review"],
    }


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> Dict[str, Any]:
    try:
        run = run_store.get(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return run.model_dump()


@router.post("/reviews/submit")
def submit_review(request: ReviewSubmitRequest) -> Dict[str, Any]:
    try:
        run = run_store.get(request.run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    listing = next(
        (item for item in run.generated_listing if item.listing_id == request.listing_id),
        None,
    )
    if not listing:
        raise HTTPException(status_code=404, detail=f"Listing not found: {request.listing_id}")

    if request.decision == "approved" and _run_has_blockers(run.compliance_report):
        raise HTTPException(
            status_code=400,
            detail="Cannot approve a run with compliance blockers in 4A MVP. Rerun compliance is not implemented.",
        )

    review = HumanReview(
        review_id=request.review_id or f"rev_{request.listing_id}",
        run_id=request.run_id,
        trace_id=request.trace_id or run.trace_id,
        listing_id=request.listing_id,
        reviewer_id=request.reviewer_id,
        decision=request.decision,
        edited_listing=request.edited_listing,
        comments=request.comments,
        edit_summary=request.edit_summary or _estimate_edit_summary(listing.model_dump(), request.edited_listing),
        human_review_result=request.human_review_result,
        reviewed_at=request.reviewed_at or utc_now_iso(),
    )

    status, current_state = _review_status(request.decision)
    updated = run_store.attach_review(run.run_id, review, status=status, current_state=current_state)

    trace = TraceRecorder()
    trace.run_node(
        "submit_review",
        {"run_id": run.run_id, "listing_id": listing.listing_id, "decision": review.decision},
        lambda: {"review_id": review.review_id, "decision": review.decision},
        lambda result: result,
    )
    updated = updated.model_copy(
        update={
            "trace_events": [*updated.trace_events, *trace.events],
            "observability": {
                **updated.observability,
                "human_review_result": review.human_review_result,
            },
            "export_payload": _export_after_review(review),
            "updated_at": utc_now_iso(),
        },
        deep=True,
    )
    run_store.save(updated)

    return {
        "run_id": updated.run_id,
        "trace_id": updated.trace_id,
        "status": updated.status,
        "review": review.model_dump(),
        "next_actions": _review_next_actions(review.decision),
    }


def _compliance_summary(reports: List[Any]) -> Dict[str, Any]:
    blocker_count = sum(report.validator_result["blocker_count"] for report in reports)
    warning_count = sum(report.validator_result["warning_count"] for report in reports)
    failed_count = sum(report.validator_result["failed_validator_count"] for report in reports)
    if blocker_count:
        overall = "blocker"
    elif warning_count:
        overall = "warning"
    else:
        overall = "pass"
    return {
        "report_count": len(reports),
        "overall_status": overall,
        "failed_validator_count": failed_count,
        "warning_count": warning_count,
        "blocker_count": blocker_count,
    }


def _validate_demo_scope(request: DemoRunRequest) -> None:
    unsupported_markets = [
        market for market in request.target_markets if market not in SUPPORTED_MARKET_LANGUAGES
    ]
    unsupported_languages = [
        language
        for language in request.target_languages
        if language not in SUPPORTED_MARKET_LANGUAGES.values()
    ]
    if unsupported_markets:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported market for 4A MVP: {', '.join(unsupported_markets)}",
        )
    if unsupported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language for 4A MVP: {', '.join(unsupported_languages)}",
        )

    invalid_pairs = [
        f"{market}/{language}"
        for market, language in zip(request.target_markets, request.target_languages)
        if SUPPORTED_MARKET_LANGUAGES[market] != language
    ]
    if invalid_pairs:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported market/language pair for 4A MVP: {', '.join(invalid_pairs)}",
        )


def _run_has_blockers(reports: List[Any]) -> bool:
    return any(report.validator_result.get("blocker_count", 0) > 0 for report in reports)


def _estimate_edit_summary(original_listing: Dict[str, Any], edited_listing: Any) -> Dict[str, Any]:
    edited = edited_listing or {}
    title_changed = "title" in edited and edited.get("title") != original_listing.get("title")
    bullet_points_changed = "bullet_points" in edited and edited.get("bullet_points") != original_listing.get("bullet_points")
    description_changed = "description" in edited and edited.get("description") != original_listing.get("description")
    attributes_changed = "attributes" in edited and edited.get("attributes") != original_listing.get("attributes")
    changed_count = sum([title_changed, bullet_points_changed, description_changed, attributes_changed])
    return {
        "title_changed": title_changed,
        "bullet_points_changed": bullet_points_changed,
        "description_changed": description_changed,
        "attributes_changed": attributes_changed,
        "estimated_edit_rate": round(changed_count / 4, 2),
    }


def _review_status(decision: str) -> tuple[str, str]:
    if decision == "approved":
        return "approved", "APPROVED"
    if decision == "rejected":
        return "rejected", "REJECTED"
    return "revision_requested", "REVISION_REQUESTED"


def _review_next_actions(decision: str) -> List[str]:
    if decision == "approved":
        return ["mock_export_available"]
    if decision == "rejected":
        return ["archive_run"]
    return ["regenerate_with_review_feedback", "rerun_compliance_check"]


def _export_after_review(review: HumanReview) -> Dict[str, Any]:
    if review.decision == "approved":
        payload = repository.get_export_payload()
        payload["is_real_platform_request"] = False
        payload["status"] = "mock_export_payload_after_review"
        return payload
    if review.decision == "changes_requested":
        return {
            "is_real_platform_request": False,
            "status": "revision_required",
            "reason": "review requested changes before mock export",
        }
    if review.decision == "rejected":
        return {
            "is_real_platform_request": False,
            "status": "not_exported",
            "reason": "review rejected",
        }
    return {"is_real_platform_request": False, "status": "not_exported"}
