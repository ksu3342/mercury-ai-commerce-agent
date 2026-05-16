# Mercury Demo Walkthrough

This is a 5-8 minute technical walkthrough for interviews, project reviews, or internal architecture reviews.

## 1. One-Line Intro

Mercury is a production-oriented MVP for a multilingual product listing and compliance Agent in cross-border commerce. It is not a production system today; the final target is a production-grade real-world AI commerce agent system.

## 2. Business Pain

Cross-border sellers need to launch product listings across markets and languages. The work is not just translation. Operators must preserve product facts, obey platform and market rules, avoid unsupported claims, keep brand terms stable, prepare export payloads, and route risky cases to human review.

The painful part is that errors are expensive: a missing EU responsible person, an invented safety claim, or an overbroad compatibility claim can block listing approval or create compliance risk.

## 3. Why This Needs An AI Agent

A normal copy generator produces text. The commerce workflow needs controlled orchestration:

- load structured product data;
- retrieve market and category rules;
- generate localized listing drafts;
- run deterministic compliance checks;
- create a human review task;
- prepare a mock export payload only when gates allow it;
- record trace events for replay and accountability.

That is why Mercury is designed as an Agent workflow with explicit nodes, not as a free-form prompt box.

## 4. Current MVP Input

The MVP input is a demo SKU and target market/language pairs:

```json
{
  "sku": "MRC-BLEND-450-WH",
  "target_markets": ["US", "DE"],
  "target_languages": ["en-US", "de-DE"]
}
```

The main walkthrough case is still the portable blender because it shows battery, food contact, multilingual copy, EU responsible person, compliance blocker, review, and mock export boundaries. LED lamp and GaN charger are backup cases to show the workflow is not hardcoded to one SKU.

## 5. POST /runs/demo

Example:

```bash
curl -X POST http://localhost:8000/runs/demo ^
  -H "Content-Type: application/json" ^
  -d "{\"sku\":\"MRC-BLEND-450-WH\",\"target_markets\":[\"US\",\"DE\"],\"target_languages\":[\"en-US\",\"de-DE\"]}"
```

The response returns `run_id`, `trace_id`, listing counts, compliance summary, and a detail link.

## 6. Workflow Nodes

`load_product` loads `ProductInput` by SKU from the case registry. Unknown SKUs return `404`; the system does not silently continue.

`retrieve_policies` uses `MockPolicyRetriever` to filter local policy chunks by market, category, and risk tags. The output includes `rule_id` and `policy_version` references.

`generate_listing` calls `MockListingGenerator`, which now depends on the `LLMProvider` abstraction. In the current MVP the provider is `MockLLMProvider`, backed by expected listing fixtures for deterministic tests and demos.

`run_compliance_check` runs `RuleEngine` validators over the generated listings. It checks required fields, title length, forbidden terms, battery fields, electrical fields, compatibility claim scope, safety claims, food-contact wording, unit consistency, and stale rule references.

`create_review_task` sets the run state. A blocker means the run is `review_required`. Even without blockers, human approval remains part of the controlled workflow.

`export_payload` returns a local adapter payload draft only when allowed. If blockers exist, the payload is blocked and has `is_real_platform_request=false`.

`write_trace` records the workflow trace so a reviewer can inspect what happened at each node.

## 7. MockPolicyRetriever

Today it does deterministic filtering over `data/shared/policy_chunks.jsonl`:

- market match: `US`, `DE`, or `ALL`;
- category match: for example `kitchen_appliance`, `home_lighting`, `consumer_electronics`, or `all`;
- risk tag match: for example `battery`, `food_contact`, `electrical_safety`, `compatibility_claim`;
- brand-term chunks are added when a product has a brand.

This is a mock retriever because the current goal is explainable, stable behavior. Production replacement would be hybrid retrieval with BM25, embeddings, metadata filters, reranker, `rule_id` citation, and `policy_version` control.

## 8. MockListingGenerator And MockLLMProvider

`MockListingGenerator` no longer owns the provider boundary. It asks an `LLMProvider` for listing JSON and converts that JSON into `GeneratedListing`.

`MockLLMProvider` returns `expected_generated_listings.json` for stable output. This keeps demos and tests repeatable. It also emits `prompt_version` and `model_info`, so future real-provider swaps do not require changing the workflow.

If asked "did you really connect an LLM?", the accurate answer is:

> Not in this MVP. I intentionally built the provider boundary and kept the default as a mock provider so tests are deterministic and no external service or API key is required. The production path is to enable an OpenAI-compatible, Qwen, DeepSeek, or enterprise gateway provider behind the same interface.

If asked "why not use a real LLM now?", the answer is:

> Because the current phase is validating architecture, workflow contracts, rule checks, and review gates. A real LLM would add output instability, cost, latency, JSON failures, and hallucination risk before the boundary is ready. The adapter skeleton is present; real provider work should come with schema validation, JSON repair, retry, fallback, evals, and cost controls.

## 9. RuleEngine

The RuleEngine handles deterministic checks that should not be delegated only to an LLM:

- missing required fields;
- EU responsible person blocker;
- title length;
- forbidden or unsupported terms;
- battery capacity and charger type preservation;
- electrical power and voltage fields;
- broad compatibility claims;
- absolute safety claims;
- food-contact wording;
- unit consistency;
- stale `rule_id` references.

LLMs can draft and explain, but deterministic validators are needed because compliance gates must be reproducible and testable.

## 10. Human Review

Human review is a compliance gate. If a blocker exists, the run cannot be approved directly. The reviewer can request changes, reject, or approve only when blockers are absent.

This is important because production systems need accountability. An Agent should assist operators, not secretly publish risky content.

## 11. Trace And Debugging

Every successful run records:

- `load_product`
- `retrieve_policies`
- `generate_listing`
- `run_compliance_check`
- `create_review_task`
- `export_payload`
- `write_trace`

`trace_id` and `trace_events` help answer: what input was loaded, which rules were retrieved, what listing was generated, which validator failed, why export was blocked, and where a failure occurred.

Trace is not just logging. In production it becomes debugging evidence, evaluation replay input, audit context, and responsibility tracking.

## 12. Why This Is Not Production Yet

Current limitations are explicit:

- local JSON data only;
- mock retriever, no vector DB;
- mock LLM provider, no external model call;
- in-memory run store;
- mock Shopify-like payload only;
- no production auth, audit, monitoring, cost control, rollback, or deployment;
- supports only demo cases and US/DE language pairs.

## 13. What Can Be Replaced Later

The replaceable modules are:

- `MockPolicyRetriever` -> hybrid retrieval / RAG service;
- `MockLLMProvider` -> OpenAI-compatible, Qwen, DeepSeek, or enterprise model gateway;
- `RuleEngine` rule source -> versioned policy service;
- `InMemoryRunStore` -> PostgreSQL;
- local cases -> PIM, ERP, OMS, platform feeds;
- mock export -> Shopify, Google Merchant, Amazon, TikTok Shop adapters;
- trace dicts -> production observability, audit, replay, monitoring.

## 14. If Reviewers Say "This Is Just Mock"

Answer directly:

> Correct. The current implementation is a production-oriented MVP, not a production system. The mocks are intentional and named honestly. They are not presented as real integrations. The engineering value is that each mock has a clear replacement path, while the core workflow, schemas, rule checks, review gate, trace, and tests already match the shape needed for production evolution.

## 15. Multi-Case Support

The system now supports three demo SKUs. This prevents the architecture from looking like a single blender hardcode:

- blender: battery, food contact, EU responsible person;
- LED lamp: electrical power field and safety claim;
- GaN charger: voltage fields and broad compatibility claim.

The cases remain small by design. They prove extension mechanics without pretending to be a real SKU catalog.

## 16. Path To A Real Business System

The production path is incremental:

1. add PostgreSQL persistence for runs, traces, reviews, compliance reports, and export jobs;
2. replace mock retrieval with policy ingestion, chunking, BM25, embeddings, metadata filters, reranking, and policy versioning;
3. enable a real LLM provider behind the existing interface with structured output and eval gates;
4. add platform adapters with dry-run, retry, rate limits, idempotency, and rollback;
5. build a human review console and audit trail;
6. add offline evaluation, monitoring, cost controls, and security governance.
