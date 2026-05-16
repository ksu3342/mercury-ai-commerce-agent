# Mock To Production Path

Mercury is currently a production-oriented MVP. It is intentionally not a production system. The table below defines how each mock or lightweight module can evolve without hiding today's limits.

| Current module | MVP current behavior | Why this is acceptable now | Production replacement | New risks after replacement | Required engineering capability | Interview / review answer |
| --- | --- | --- | --- | --- | --- | --- |
| `MockPolicyRetriever` | Filters local `policy_chunks.jsonl` by market, category, risk tags, and brand term. | Deterministic, explainable, no vector DB dependency. | Hybrid retrieval with BM25, embedding search, metadata filter, reranker, `rule_id` citation, `policy_version` control. | Wrong recall, stale policies, bad chunking, reranker drift, citation mismatch. | Policy ingestion, chunking, index builds, eval set, versioning, rollback, retrieval metrics. | It is a mock retriever today; the interface is shaped so production RAG can replace it without changing workflow nodes. |
| `MockListingGenerator` | Calls `MockLLMProvider` and converts JSON to `GeneratedListing`. | Keeps demo stable while exercising provider boundary and schema conversion. | Real provider through `LLMProvider`: OpenAI-compatible API, Qwen, DeepSeek, or enterprise gateway. | JSON invalidity, hallucination, prompt drift, latency, cost, unsafe output. | Structured output, schema validation, JSON repair, retry/fallback, prompt versioning, model tracking, eval regression. | The generator is not the model; it is the boundary that lets us swap providers later. |
| `RuleEngine` | Deterministic checks for required fields, forbidden terms, battery, electrical, compatibility, safety, food-contact, unit consistency, stale rule refs. | Critical checks stay reproducible and testable. | Versioned rule engine fed by policy service and rule management UI. | Rule conflicts, stale rules, false positives/negatives, policy owner disputes. | Rule versioning, test fixtures, review workflow, override policy, audit log. | Even with real LLMs, deterministic validators remain necessary because compliance cannot rely only on model judgment. |
| `InMemoryRunStore` | Stores runs in process memory. | Simple for local tests and demo walkthroughs. | PostgreSQL tables: `run`, `trace`, `review`, `compliance_report`, `export_job`. | Migration errors, concurrency, partial writes, retention, data privacy. | Transaction boundaries, migrations, indexes, backup/restore, retention policy. | This is deliberately non-persistent; persistence is the next production step. |
| `DemoDataRepository` | Loads local JSON cases and shared JSONL rules. | Fast, inspectable, no external service. | PostgreSQL, object storage, internal product master data, platform feed data, PIM/ERP/OMS integration. | Data freshness, schema drift, missing attributes, source conflict. | Data contracts, ingestion jobs, validation, lineage, reconciliation. | Local JSON proves shape; real product data belongs behind the same repository boundary. |
| Export payload | Returns Shopify-like adapter draft with `is_real_platform_request=false`. | Shows adapter shape without pretending to publish. | Shopify Admin API, Google Merchant feed, Amazon/TikTok Shop adapters with retry, rate limits, idempotency key, rollback. | Duplicate exports, rate-limit failures, partial publication, rollback gaps. | Adapter contracts, dry-run mode, idempotency, retry policy, dead-letter handling, rollback records. | The payload is a draft, not a platform request. Real adapters are future work. |
| Observability / trace | Stores node events in the run response. | Enough for local debugging and demo replay. | Structured logs, traces, metrics, eval replay store, audit events. | Sensitive data exposure, noisy logs, missing correlation IDs. | Trace schema, log redaction, metrics, alerting, replay tooling. | Observability is not just logs; it supports problem diagnosis, eval replay, and accountability. |
| Human review | Review endpoint supports approve, changes requested, rejected. Blockers cannot be approved. | Establishes risk-control gate before UI exists. | Review console with queues, assignments, comments, approvals, overrides, audit trail. | Reviewer mistakes, bypass pressure, SLA delays, unclear ownership. | RBAC, audit log, review policy, escalation path, override controls. | Human review is a production risk-control node, not decoration. |
| Market/language validation | Hardcoded US/en-US and DE/de-DE pairs. | Prevents accidental unsupported locale assumptions. | Market config service with supported locales, currency, units, platform rules. | Bad locale mapping, partial translations, market-specific policy gaps. | Config management, validation tests, rollout controls. | The MVP rejects unsupported pairs instead of guessing. |
| Evaluation dataset | Demo tests plus expected listings and compliance reports. | Small but repeatable regression base. | Offline golden set across SKUs, markets, languages, policies, and failure modes. | Eval blind spots, stale golden data, metric gaming. | Dataset curation, annotation, scoring rubric, CI regression, drift monitoring. | The current cases are seeds, not claims of broad coverage. |
| Platform adapter | No real adapter, only local draft. | Avoids unsafe external side effects. | Adapter layer per platform with dry-run, submit, status poll, rollback. | API changes, auth failures, idempotency bugs, compliance rejection. | Adapter abstraction, contract tests, sandbox tests, retry/rate-limit control. | Real platform integration should come after gates and persistence. |
| Policy rule management | Local `policy_rules.jsonl` and `policy_chunks.jsonl`. | Transparent and easy to diff. | Versioned policy service with ingestion, approval workflow, active version, rollback. | Unapproved rule changes, stale versions, rule conflicts. | Policy ownership, governance, tests, migration tooling. | Local JSONL is the fixture version of a future policy service. |
| Prompt/version management | Prompt constants and `prompt_version` in provider output. | Enough to prove traceability. | Prompt registry with versioned templates, rollout, A/B eval, rollback. | Prompt drift, hidden behavior changes, bad rollback. | Prompt registry, eval gate, model/prompt matrix, release notes. | `prompt_version` exists now so future model outputs can be traced. |
| Cost and latency control | No real model calls, so no model cost. | Avoids false cost claims. | Token accounting, provider timeout, batching, caching, fallback, budget alerts. | Cost spikes, slow runs, provider outage. | Cost telemetry, latency SLOs, fallback policy, cache invalidation. | No evidence indicates current MVP has real LLM cost or latency behavior. |
| Audit and rollback | Trace and mock export status only. | Sufficient for local review of demo runs. | Immutable audit log, export snapshots, rollback jobs, policy/model version replay. | Incomplete audit chain, rollback side effects, legal retention. | Append-only audit, snapshot storage, rollback adapter, replay tools. | Production rollback is designed as a future requirement, not claimed today. |

## Hybrid Retrieval Target

`MockPolicyRetriever` should become a retrieval service with:

- BM25 for lexical policy matches;
- embedding search for semantic matches;
- metadata filters for market, language, category, platform, policy version, and risk tag;
- reranker for final ordering;
- `rule_id` citation in every retrieved chunk;
- `policy_version` control for replay and rollback.

## LLM Provider Target

`MockLLMProvider` should evolve into:

- OpenAI-compatible API provider;
- Qwen / DeepSeek compatible provider;
- enterprise model gateway provider;
- structured output enforcement;
- JSON schema validation;
- JSON repair for common malformed output;
- `prompt_version` tracking;
- `model_info` tracking;
- regression evaluation against golden cases.

## Persistence Target

`InMemoryRunStore` should become PostgreSQL:

- `run` table for request, state, product snapshot, status;
- `trace` table for node-level events;
- `review` table for reviewer decisions and edits;
- `compliance_report` table for issues and validator summaries;
- `export_job` table for adapter drafts, submissions, retries, and rollback records.

## Data Source Target

Local JSON should become a combination of:

- PostgreSQL for transactional run and review data;
- object storage for large product assets and snapshots;
- internal product master data from PIM/ERP/OMS;
- platform feed data from Shopify, Google Merchant, Amazon, or TikTok Shop.

## Export Target

Mock export should become platform adapters:

- Shopify Admin API adapter;
- Google Merchant feed adapter;
- Amazon / TikTok Shop adapter;
- dry-run mode;
- retry and rate-limit control;
- idempotency key;
- rollback and export snapshot.

## Multi-Case To Real SKU Library

The three demo cases are regression seeds. A real SKU library needs product master integration, category-specific validators, policy coverage by market, and golden cases for each major risk family. Multi-case support should then become a regression evaluation set, not just demo data.
