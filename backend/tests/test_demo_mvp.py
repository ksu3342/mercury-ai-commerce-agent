import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.generators.mock_listing import MockListingGenerator
from app.main import app
from app.repositories.demo_data import DemoDataRepository
from app.retrievers.mock_policy import MockPolicyRetriever
from app.validators.rule_engine import RuleEngine


DEMO_REQUEST = {
    "sku": "MRC-BLEND-450-WH",
    "target_markets": ["US", "DE"],
    "target_languages": ["en-US", "de-DE"],
}


def test_demo_run_success():
    client = TestClient(app)

    response = client.post("/runs/demo", json=DEMO_REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "run_demo_blender_001"
    assert body["trace_id"] == "trc_demo_blender_001"
    assert body["status"] == "review_required"
    assert body["generated_listing_summary"]["listing_count"] == 2
    assert body["compliance_summary"]["blocker_count"] >= 1
    assert "/runs/run_demo_blender_001" in body["links"]["run_detail"]


def test_policy_retriever_returns_canonical_rule_ids():
    repo = DemoDataRepository()
    product = repo.get_product_by_sku("MRC-BLEND-450-WH")
    retriever = MockPolicyRetriever(repo)

    chunks = retriever.retrieve(
        product=product,
        target_market="DE",
        category=product.category_hint,
        regulatory_tags=product.regulatory_tags,
    )

    rule_ids = {chunk.rule_id for chunk in chunks}
    assert "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED" in rule_ids
    assert "FOOD_CONTACT_MATERIAL_DISCLOSURE" in rule_ids
    assert "BRAND_TERM_DO_NOT_TRANSLATE" in rule_ids
    assert all(chunk.chunk_id and chunk.policy_version for chunk in chunks)


def test_rule_engine_detects_battery_and_food_contact_risks():
    repo = DemoDataRepository()
    product = repo.get_product_by_sku("MRC-BLEND-450-WH")
    generator = MockListingGenerator(repo)
    listings = generator.generate(
        product=product,
        target_markets=["US", "DE"],
        target_languages=["en-US", "de-DE"],
        retrieved_chunks=repo.get_rag_chunks(),
    )

    reports = RuleEngine(
        policy_rules=repo.get_policy_rules(),
        market_configs=repo.get_market_configs(),
    ).check(product=product, listings=listings)

    issue_rule_ids = {
        issue.rule_id
        for report in reports
        for issue in report.checks
    }
    de_report = next(report for report in reports if report.market_id == "DE")

    assert "BATTERY_CAPACITY_FIELD_REQUIRED" in issue_rule_ids
    assert "FOOD_CONTACT_MATERIAL_DISCLOSURE" in issue_rule_ids
    assert "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED" in issue_rule_ids
    assert de_report.overall_status == "blocker"


def test_get_run_returns_trace():
    client = TestClient(app)
    client.post("/runs/demo", json=DEMO_REQUEST)

    response = client.get("/runs/run_demo_blender_001")

    assert response.status_code == 200
    body = response.json()
    node_names = [event["node_name"] for event in body["trace_events"]]
    assert body["product_input"]["sku"] == "MRC-BLEND-450-WH"
    assert body["retrieved_chunks"]
    assert "load_product" in node_names
    assert "write_trace" in node_names


def test_review_submit_updates_run():
    client = TestClient(app)
    client.post("/runs/demo", json=DEMO_REQUEST)
    project_root = Path(__file__).resolve().parents[2]
    review_payload = json.loads(
        (project_root / "data" / "demo" / "human_review.json").read_text(encoding="utf-8")
    )

    response = client.post("/reviews/submit", json=review_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["review"]["decision"] == "changes_requested"
    assert body["status"] == "revision_requested"

    run_response = client.get("/runs/run_demo_blender_001")
    run_body = run_response.json()
    assert run_body["human_review"]["review_id"] == "rev_demo_blender_de"
    assert run_body["human_review"]["human_review_result"]["needs_regeneration"] is False
