# Mercury Backend MVP

This backend is a minimal FastAPI implementation for the Mercury Portfolio PoC / Business Simulation Project. It runs the fixed Portable Blender demo case from `data/demo` through a deterministic workflow graph.

It does not call real LLM providers, Shopify, Google Merchant, Amazon, PostgreSQL, Redis, Milvus, or LangGraph.

## Install

```bash
cd backend
python -m pip install -r requirements.txt
```

## Run The API

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Run Tests

```bash
python -m pytest backend/tests -q
```

or from `backend/`:

```bash
python -m pytest tests -q
```

## Demo Request

```bash
curl -X POST http://localhost:8000/runs/demo ^
  -H "Content-Type: application/json" ^
  -d "{\"sku\":\"MRC-BLEND-450-WH\",\"target_markets\":[\"US\",\"DE\"],\"target_languages\":[\"en-US\",\"de-DE\"]}"
```

Expected response shape:

```json
{
  "run_id": "run_demo_blender_001",
  "trace_id": "trc_demo_blender_001",
  "status": "review_required",
  "generated_listing_summary": {
    "listing_count": 2,
    "markets": ["US", "DE"],
    "languages": ["en-US", "de-DE"]
  },
  "compliance_summary": {
    "report_count": 2,
    "overall_status": "blocker",
    "failed_validator_count": 1,
    "warning_count": 3,
    "blocker_count": 1
  },
  "links": {
    "run_detail": "/runs/run_demo_blender_001"
  },
  "next_actions": ["submit_review", "fix_blockers"]
}
```

Then inspect the full run:

```bash
curl http://localhost:8000/runs/run_demo_blender_001
```

Submit the demo review:

```bash
curl -X POST http://localhost:8000/reviews/submit ^
  -H "Content-Type: application/json" ^
  -d @../data/demo/human_review.json
```

## What Is Mocked

- `MockPolicyRetriever`: filters local `policy_chunks.jsonl` by market, category and regulatory tags. It does not use embeddings.
- `MockListingGenerator`: reads `expected_generated_listings.json` first. If a listing is missing, it falls back to a fact-only template and marks missing required fields instead of inventing them.
- `RuleEngine`: deterministic validators only. It checks required fields, title length, forbidden terms, battery fields, food-contact wording, basic unit consistency and retrieved `rule_id` references.
- `Export payload`: returns a local Shopify-like JSON object. It is not a real Shopify Admin API request.
- `RunStore`: in-memory only. Restarting the API clears run state.

## Replacement Path

- Replace `MockListingGenerator` with an `LLMProvider.generate_json` adapter after schema validation and JSON repair are in place.
- Replace `MockPolicyRetriever` with hybrid retrieval over a real vector store only after the local rule corpus and metadata filters are stable.
- Replace the in-memory `RunStore` with PostgreSQL when multiple runs or persistence matter.
- Replace the mock export payload with real platform adapters only after review and compliance gates are enforced.

## Known Inconsistencies

- `data/demo/policy_chunks.jsonl` uses `version`; the API returns this as `policy_version` because the project spec uses `policy_version` for observability and traceability.
- Historical docs and data examples use `check_id` and `suggested_fix`; this backend accepts those aliases but emits `issue_id` and `suggestion` inside `ComplianceIssue`, matching the backend MVP requirement.
- `policy_chunks.jsonl` has no `platform` metadata. The MVP retriever filters by market, category and regulatory tags; platform can be added later without changing API shape.
- Unit consistency has no canonical rule in `policy_rules.jsonl`. The MVP implements the check and would emit `UNIT_CONSISTENCY_BASIC` only if a mismatch is detected.
