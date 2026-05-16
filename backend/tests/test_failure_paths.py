from fastapi.testclient import TestClient

from app.main import app
from app.repositories.demo_data import DemoDataRepository
from app.schemas import RetrievedChunkRef
from app.validators.rule_engine import RuleEngine


DEMO_REQUEST = {
    "sku": "MRC-BLEND-450-WH",
    "target_markets": ["US", "DE"],
    "target_languages": ["en-US", "de-DE"],
}


def test_demo_run_unknown_sku_returns_404():
    client = TestClient(app)

    response = client.post(
        "/runs/demo",
        json={
            "sku": "MRC-UNKNOWN-SKU",
            "target_markets": ["US"],
            "target_languages": ["en-US"],
        },
    )

    assert response.status_code == 404
    assert "Product SKU not found" in response.json()["detail"]


def test_demo_run_unsupported_language_returns_400():
    client = TestClient(app)

    response = client.post(
        "/runs/demo",
        json={
            "sku": "MRC-BLEND-450-WH",
            "target_markets": ["US"],
            "target_languages": ["es-ES"],
        },
    )

    assert response.status_code == 400
    assert "Unsupported language" in response.json()["detail"]


def test_demo_run_invalid_market_language_pair_returns_400():
    client = TestClient(app)

    response = client.post(
        "/runs/demo",
        json={
            "sku": "MRC-BLEND-450-WH",
            "target_markets": ["US"],
            "target_languages": ["de-DE"],
        },
    )

    assert response.status_code == 400
    assert "Unsupported market/language pair" in response.json()["detail"]


def test_get_run_not_found_returns_404():
    client = TestClient(app)

    response = client.get("/runs/run_missing_001")

    assert response.status_code == 404
    assert "Run not found" in response.json()["detail"]


def test_review_unknown_run_returns_404():
    client = TestClient(app)

    response = client.post(
        "/reviews/submit",
        json={
            "run_id": "run_missing_001",
            "listing_id": "lst_missing_001",
            "reviewer_id": "reviewer_demo_01",
            "decision": "changes_requested",
            "human_review_result": {"needs_regeneration": True},
        },
    )

    assert response.status_code == 404
    assert "Run not found" in response.json()["detail"]


def test_review_unknown_listing_returns_404():
    client = TestClient(app)
    run = client.post("/runs/demo", json=DEMO_REQUEST).json()

    response = client.post(
        "/reviews/submit",
        json={
            "run_id": run["run_id"],
            "listing_id": "lst_missing_001",
            "reviewer_id": "reviewer_demo_01",
            "decision": "changes_requested",
            "human_review_result": {"needs_regeneration": True},
        },
    )

    assert response.status_code == 404
    assert "Listing not found" in response.json()["detail"]


def test_trace_contains_all_core_nodes():
    client = TestClient(app)
    run = client.post("/runs/demo", json=DEMO_REQUEST).json()

    response = client.get(run["links"]["run_detail"])

    assert response.status_code == 200
    node_names = [event["node_name"] for event in response.json()["trace_events"]]
    assert node_names == [
        "load_product",
        "retrieve_policies",
        "generate_listing",
        "run_compliance_check",
        "create_review_task",
        "export_payload",
        "write_trace",
    ]


def test_export_blocked_before_review_when_blocker_exists():
    client = TestClient(app)
    run = client.post("/runs/demo", json=DEMO_REQUEST).json()

    response = client.get(run["links"]["run_detail"])

    assert response.status_code == 200
    export_payload = response.json()["export_payload"]
    assert export_payload["is_real_platform_request"] is False
    assert export_payload["status"] == "blocked_until_human_review"
    assert "items" not in export_payload


def test_rule_reference_warning_for_unknown_rule_id():
    repo = DemoDataRepository()
    product = repo.get_product_by_sku("MRC-BLEND-450-WH")
    listing = repo.get_expected_listings()[0].model_copy(
        update={
            "retrieved_chunks": [
                *repo.get_expected_listings()[0].retrieved_chunks,
                RetrievedChunkRef(
                    chunk_id="policy_stale_001",
                    rule_id="STALE_RULE_ID",
                    source="mock_policy_pack",
                ),
            ]
        },
        deep=True,
    )

    report = RuleEngine(
        policy_rules=repo.get_policy_rules(),
        market_configs=repo.get_market_configs(),
    ).check(product=product, listings=[listing])[0]

    stale_rule_checks = [
        issue for issue in report.checks if issue.rule_id == "STALE_RULE_ID"
    ]
    assert stale_rule_checks
    assert stale_rule_checks[0].status == "warning"
