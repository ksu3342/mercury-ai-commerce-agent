# Mercury Backend MVP

Mercury is a production-oriented MVP for a multilingual product listing and compliance growth Agent. The final target is a production-grade real-world AI commerce agent system, but the current backend is still a lightweight, local, testable prototype.

It does not call real LLM providers, Shopify, Google Merchant, Amazon, PostgreSQL, Redis, Milvus, LangGraph, or any external production service.

## Current Scope

The backend runs a controlled workflow through:

1. `load_product`
2. `retrieve_policies`
3. `generate_listing`
4. `run_compliance_check`
5. `create_review_task`
6. `export_payload`
7. `write_trace`

Supported demo cases:

| SKU | Case | Markets | Languages | Main risks |
| --- | --- | --- | --- | --- |
| `MRC-BLEND-450-WH` | Portable blender | US, DE | en-US, de-DE | battery fields, food contact wording, EU responsible person |
| `MRC-LAMP-LED-001` | LED desk lamp | US, DE | en-US, de-DE | electrical power field, energy/power rating, safety claim, EU responsible person |
| `MRC-CHARGER-65W` | USB-C GaN charger | US, DE | en-US, de-DE | power/voltage fields, broad compatibility claim, EU responsible person |

These are demo cases, not a real product catalog. The multi-case structure exists to prove the workflow is not hardcoded to one blender SKU and can later move toward a real SKU library.

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

Run everything:

```bash
cd backend
python -m pytest tests -q
```

Run failure-path coverage only:

```bash
python -m pytest tests/test_failure_paths.py -q
```

Run multi-case coverage only:

```bash
python -m pytest tests/test_multi_case.py -q
```

Run LLM provider boundary coverage only:

```bash
python -m pytest tests/test_llm_provider.py -q
```

## Demo Request

```bash
curl -X POST http://localhost:8000/runs/demo ^
  -H "Content-Type: application/json" ^
  -d "{\"sku\":\"MRC-BLEND-450-WH\",\"target_markets\":[\"US\",\"DE\"],\"target_languages\":[\"en-US\",\"de-DE\"]}"
```

Example response shape:

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
    "warning_count": 1,
    "blocker_count": 1
  },
  "links": {
    "run_detail": "/runs/run_demo_blender_001"
  },
  "next_actions": ["submit_review", "fix_blockers"]
}
```

Inspect the full run:

```bash
curl http://localhost:8000/runs/run_demo_blender_001
```

Submit the blender demo review:

```bash
curl -X POST http://localhost:8000/reviews/submit ^
  -H "Content-Type: application/json" ^
  -d @../data/cases/blender/human_review.json
```

## Failure Path Behavior

The current API has explicit failure semantics:

| Scenario | Status | Meaning |
| --- | --- | --- |
| Unknown `sku` | `404` | The case registry has no matching product input. |
| Unsupported market | `400` | The MVP only supports US and DE. |
| Unsupported language | `400` | The MVP only supports en-US and de-DE. |
| Invalid market/language pair such as `US/de-DE` | `400` | Locale routing is explicit; the API does not guess. |
| Unknown `run_id` | `404` | In-memory run state has no matching run. |
| Unknown `listing_id` during review | `404` | Review must target a listing generated in that run. |
| Approving a run with blockers | `400` | Blockers cannot bypass the review gate. |

This is intentional: silent success would hide business risk.

## Review Gate

The review endpoint is not an auto-publish API.

- `approved` can produce a mock export payload only when the run has no compliance blocker.
- `changes_requested` keeps `export_payload.status` as `revision_required`.
- `rejected` keeps `export_payload.status` as `not_exported`.
- A run with blockers cannot be approved directly in this MVP because rerun-after-edit compliance checking is not implemented yet.

Human review is treated as a risk-control gate. It is not a UI convenience.

## Mock Boundaries

- `MockPolicyRetriever`: deterministic metadata filtering over local `data/shared/policy_chunks.jsonl`; no BM25, embeddings, reranker, or vector database.
- `MockLLMProvider`: stable provider boundary backed by `expected_generated_listings.json`; no network calls and no API key.
- `MockListingGenerator`: converts provider JSON into `GeneratedListing` models and enriches retrieved chunk references.
- `RuleEngine`: deterministic validators for required fields, title length, forbidden terms, battery fields, electrical fields, compatibility claim scope, safety claims, food-contact wording, unit consistency, and stale rule references.
- `InMemoryRunStore`: process-local state only; restart clears runs.
- `Export payload`: local Shopify-like adapter draft with `is_real_platform_request=false`; not a Shopify Admin API request.

## LLM Provider Boundary

Default provider:

```text
MockLLMProvider
```

It returns fixture-backed JSON with:

- `prompt_version`
- `model_info.provider = "mock_llm"`
- schema-compatible listing payloads

`OpenAICompatibleProvider` exists only as a disabled skeleton. It documents the future adapter shape for OpenAI-compatible APIs, Qwen, DeepSeek, or an enterprise model gateway. Tests must not call a real LLM or require an API key.

Future real-provider work must add provider config, structured output, JSON schema validation, JSON repair, retry/fallback, cost and latency tracking, prompt versioning, model versioning, and regression evaluation.

## Data Layout

```text
data/cases/
  blender/
  led_lamp/
  gan_charger/

data/shared/
  market_configs.json
  policy_rules.jsonl
  policy_chunks.jsonl
  brand_terms.json
  forbidden_terms.json
```

`data/demo` is retained as the original 4A fixture for historical compatibility. New development should prefer `data/cases/*` plus `data/shared/*`.

## Replacement Path

| MVP module | Production replacement |
| --- | --- |
| `MockPolicyRetriever` | Hybrid retrieval: BM25, embedding search, metadata filter, reranker, `rule_id` citation, `policy_version` control |
| `MockLLMProvider` | Real OpenAI-compatible, Qwen, DeepSeek, or enterprise model gateway provider |
| `InMemoryRunStore` | PostgreSQL tables for runs, traces, reviews, compliance reports, and export jobs |
| Local JSON product cases | PIM, ERP, OMS, platform feed, PostgreSQL, and object storage |
| Mock export payload | Shopify Admin API, Google Merchant feed, Amazon/TikTok adapters with retry, rate limit, idempotency, dry-run, rollback |
| Trace events | Structured observability for debugging, replay, evaluation, audit, and accountability |

## Current Non-Claims

Do not claim this backend:

- is production deployed;
- serves real customers;
- calls a real online LLM;
- integrates real Shopify, Google Merchant, Amazon, or TikTok Shop APIs;
- uses a real vector database;
- has production-grade auth, audit, concurrency, monitoring, rollback, or deployment;
- can fully automate legal or platform compliance;
- supports arbitrary products and arbitrary markets.

The accurate claim is: this is a production-oriented MVP that runs a multi-case Agent backend loop and preserves clear replacement boundaries for future production work.
