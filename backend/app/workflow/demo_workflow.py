from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.generators import MockListingGenerator
from app.observability import TraceRecorder
from app.repositories import DemoDataRepository, InMemoryRunStore
from app.retrievers import MockPolicyRetriever
from app.schemas import (
    ComplianceReport,
    DemoRunRequest,
    GeneratedListing,
    HumanReview,
    ProductInput,
    RagChunk,
    RunSummary,
    TraceEvent,
)
from app.validators import RuleEngine


RUN_ID = "run_demo_blender_001"
TRACE_ID = "trc_demo_blender_001"


@dataclass
class WorkflowState:
    request: DemoRunRequest
    run_id: str = RUN_ID
    trace_id: str = TRACE_ID
    status: str = "received"
    current_state: str = "RECEIVED"
    product: Optional[ProductInput] = None
    retrieved_chunks: List[RagChunk] = field(default_factory=list)
    listings: List[GeneratedListing] = field(default_factory=list)
    reports: List[ComplianceReport] = field(default_factory=list)
    human_review: Optional[HumanReview] = None
    export_payload: Dict[str, Any] = field(default_factory=dict)
    trace_events: List[TraceEvent] = field(default_factory=list)


class DemoWorkflow:
    def __init__(
        self,
        repository: DemoDataRepository,
        run_store: InMemoryRunStore,
        retriever: MockPolicyRetriever,
        generator: MockListingGenerator,
        rule_engine: RuleEngine,
    ) -> None:
        self.repository = repository
        self.run_store = run_store
        self.retriever = retriever
        self.generator = generator
        self.rule_engine = rule_engine

    def run(self, request: DemoRunRequest) -> RunSummary:
        state = WorkflowState(request=request)
        trace = TraceRecorder()

        state.product = trace.run_node(
            "load_product",
            {"sku": request.sku},
            lambda: self._load_product(request.sku),
            lambda product: {
                "product_id": product.product_id,
                "sku": product.sku,
                "category_hint": product.category_hint,
            },
        )

        state.retrieved_chunks = trace.run_node(
            "retrieve_policies",
            {
                "target_markets": request.target_markets,
                "category": state.product.category_hint,
                "regulatory_tags": state.product.regulatory_tags,
            },
            lambda: self._retrieve_policies(state),
            lambda chunks: {
                "chunk_count": len(chunks),
                "rule_ids": sorted({chunk.rule_id for chunk in chunks if chunk.rule_id}),
            },
        )

        state.listings = trace.run_node(
            "generate_listing",
            {"target_markets": request.target_markets, "target_languages": request.target_languages},
            lambda: self._generate_listing(state),
            lambda listings: {
                "listing_count": len(listings),
                "listing_ids": [listing.listing_id for listing in listings],
            },
        )

        state.reports = trace.run_node(
            "run_compliance_check",
            {"listing_ids": [listing.listing_id for listing in state.listings]},
            lambda: self._run_compliance_check(state),
            lambda reports: {
                "report_count": len(reports),
                "overall_status": self._overall_status(reports),
                "blocker_count": self._blocker_count(reports),
            },
        )

        trace.run_node(
            "create_review_task",
            {"blocker_count": self._blocker_count(state.reports)},
            lambda: self._create_review_task(state),
            lambda task: task,
        )

        state.export_payload = trace.run_node(
            "export_payload",
            {"status": state.status},
            lambda: self._export_payload(state),
            lambda payload: {
                "is_real_platform_request": payload.get("is_real_platform_request", False),
                "status": payload.get("status", "mock_payload_ready"),
            },
        )

        trace.run_node(
            "write_trace",
            {"run_id": state.run_id},
            lambda: {"event_count": len(trace.events) + 1},
            lambda result: result,
        )
        state.trace_events = trace.events

        summary = self._to_run_summary(state)
        return self.run_store.save(summary)

    def _load_product(self, sku: str) -> ProductInput:
        return self.repository.get_product_by_sku(sku)

    def _retrieve_policies(self, state: WorkflowState) -> List[RagChunk]:
        assert state.product is not None
        chunks_by_id: Dict[str, RagChunk] = {}
        for market_id in state.request.target_markets:
            chunks = self.retriever.retrieve(
                product=state.product,
                target_market=market_id,
                category=state.product.category_hint,
                regulatory_tags=state.product.regulatory_tags,
            )
            for chunk in chunks:
                chunks_by_id[chunk.chunk_id] = chunk
        return sorted(chunks_by_id.values(), key=lambda item: item.score, reverse=True)

    def _generate_listing(self, state: WorkflowState) -> List[GeneratedListing]:
        assert state.product is not None
        return self.generator.generate(
            product=state.product,
            target_markets=state.request.target_markets,
            target_languages=state.request.target_languages,
            retrieved_chunks=state.retrieved_chunks,
            run_id=state.run_id,
            trace_id=state.trace_id,
        )

    def _run_compliance_check(self, state: WorkflowState) -> List[ComplianceReport]:
        assert state.product is not None
        return self.rule_engine.check(product=state.product, listings=state.listings)

    def _create_review_task(self, state: WorkflowState) -> Dict[str, Any]:
        blocker_count = self._blocker_count(state.reports)
        if blocker_count:
            state.status = "review_required"
            state.current_state = "REVIEW_REQUIRED"
            return {"review_required": True, "reason": "blocker_count > 0"}
        state.status = "ready_for_review"
        state.current_state = "READY_FOR_REVIEW"
        return {"review_required": True, "reason": "human approval required before mock export"}

    def _export_payload(self, state: WorkflowState) -> Dict[str, Any]:
        if self._blocker_count(state.reports):
            return {
                "is_real_platform_request": False,
                "status": "blocked_until_human_review",
                "reason": "compliance blockers must be reviewed before mock export",
            }
        payload = self.repository.get_export_payload()
        payload["is_real_platform_request"] = False
        return payload

    def _to_run_summary(self, state: WorkflowState) -> RunSummary:
        assert state.product is not None
        observability = self._observability(state)
        return RunSummary(
            run_id=state.run_id,
            trace_id=state.trace_id,
            status=state.status,
            current_state=state.current_state,
            product_input=state.product,
            retrieved_chunks=state.retrieved_chunks,
            generated_listing=state.listings,
            compliance_report=state.reports,
            human_review=state.human_review,
            export_payload=state.export_payload,
            trace_events=state.trace_events,
            observability=observability,
        )

    def _observability(self, state: WorkflowState) -> Dict[str, Any]:
        failed = sum(report.validator_result["failed_validator_count"] for report in state.reports)
        warnings = sum(report.validator_result["warning_count"] for report in state.reports)
        blockers = sum(report.validator_result["blocker_count"] for report in state.reports)
        return {
            "prompt_version": "listing_generator_v1.0.0",
            "policy_version": "demo-policy-2026-05",
            "retrieved_chunks": [
                {"chunk_id": chunk.chunk_id, "rule_id": chunk.rule_id, "policy_version": chunk.policy_version}
                for chunk in state.retrieved_chunks
            ],
            "validator_result": {
                "failed_validator_count": failed,
                "warning_count": warnings,
                "blocker_count": blockers,
            },
            "human_review_result": None,
        }

    def _overall_status(self, reports: List[ComplianceReport]) -> str:
        if any(report.overall_status == "blocker" for report in reports):
            return "blocker"
        if any(report.overall_status == "warning" for report in reports):
            return "warning"
        return "pass"

    def _blocker_count(self, reports: List[ComplianceReport]) -> int:
        return sum(report.validator_result["blocker_count"] for report in reports)
