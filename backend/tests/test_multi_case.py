from fastapi.testclient import TestClient

from app.main import app
from app.repositories.demo_data import DemoDataRepository
from app.retrievers.mock_policy import MockPolicyRetriever


LED_REQUEST = {
    "sku": "MRC-LAMP-LED-001",
    "target_markets": ["US", "DE"],
    "target_languages": ["en-US", "de-DE"],
}

CHARGER_REQUEST = {
    "sku": "MRC-CHARGER-65W",
    "target_markets": ["US", "DE"],
    "target_languages": ["en-US", "de-DE"],
}


def test_demo_run_led_lamp_success():
    client = TestClient(app)

    response = client.post("/runs/demo", json=LED_REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "run_demo_mrc_lamp_led_001"
    assert body["generated_listing_summary"]["listing_count"] == 2
    assert body["compliance_summary"]["blocker_count"] >= 1


def test_demo_run_gan_charger_success():
    client = TestClient(app)

    response = client.post("/runs/demo", json=CHARGER_REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "run_demo_mrc_charger_65w"
    assert body["generated_listing_summary"]["listing_count"] == 2
    assert body["compliance_summary"]["warning_count"] >= 1


def test_case_specific_policy_rules_retrieved():
    repo = DemoDataRepository()
    retriever = MockPolicyRetriever(repo)
    lamp = repo.get_product_by_sku("MRC-LAMP-LED-001")
    charger = repo.get_product_by_sku("MRC-CHARGER-65W")

    lamp_rule_ids = {
        chunk.rule_id
        for chunk in retriever.retrieve(
            product=lamp,
            target_market="US",
            category=lamp.category_hint,
            regulatory_tags=lamp.regulatory_tags,
        )
    }
    charger_rule_ids = {
        chunk.rule_id
        for chunk in retriever.retrieve(
            product=charger,
            target_market="US",
            category=charger.category_hint,
            regulatory_tags=charger.regulatory_tags,
        )
    }

    assert "ELECTRICAL_POWER_FIELD_REQUIRED" in lamp_rule_ids
    assert "SAFETY_CLAIM_NEEDS_EVIDENCE" in lamp_rule_ids
    assert "COMPATIBILITY_CLAIM_NEEDS_SCOPE" in charger_rule_ids
    assert "BATTERY_CAPACITY_FIELD_REQUIRED" not in lamp_rule_ids


def test_case_specific_compliance_issue_detected():
    client = TestClient(app)

    lamp_run = client.post("/runs/demo", json=LED_REQUEST).json()
    charger_run = client.post("/runs/demo", json=CHARGER_REQUEST).json()

    lamp_detail = client.get(lamp_run["links"]["run_detail"]).json()
    charger_detail = client.get(charger_run["links"]["run_detail"]).json()
    lamp_issue_ids = {
        issue["rule_id"]
        for report in lamp_detail["compliance_report"]
        for issue in report["checks"]
        if issue["status"] in {"warning", "failed"}
    }
    charger_issue_ids = {
        issue["rule_id"]
        for report in charger_detail["compliance_report"]
        for issue in report["checks"]
        if issue["status"] in {"warning", "failed"}
    }

    assert "ELECTRICAL_POWER_FIELD_REQUIRED" in lamp_issue_ids
    assert "SAFETY_CLAIM_NEEDS_EVIDENCE" in lamp_issue_ids
    assert "COMPATIBILITY_CLAIM_NEEDS_SCOPE" in charger_issue_ids


def test_unknown_case_sku_returns_404():
    client = TestClient(app)

    response = client.post(
        "/runs/demo",
        json={
            "sku": "MRC-CASE-NOT-FOUND",
            "target_markets": ["US"],
            "target_languages": ["en-US"],
        },
    )

    assert response.status_code == 404


def test_multi_case_runs_do_not_overwrite_each_other():
    client = TestClient(app)

    lamp = client.post("/runs/demo", json=LED_REQUEST).json()
    charger = client.post("/runs/demo", json=CHARGER_REQUEST).json()

    assert lamp["run_id"] != charger["run_id"]
    lamp_detail = client.get(lamp["links"]["run_detail"]).json()
    charger_detail = client.get(charger["links"]["run_detail"]).json()
    assert lamp_detail["product_input"]["sku"] == "MRC-LAMP-LED-001"
    assert charger_detail["product_input"]["sku"] == "MRC-CHARGER-65W"
