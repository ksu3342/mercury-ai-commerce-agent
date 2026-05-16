# Mercury Resume Bullets

These bullets separate the current truthful version from interview framing and future-target wording. Do not claim real production deployment, real customers, real business metrics, real platform API integration, or complete compliance automation unless those facts are later implemented and evidenced.

## A. Current Truthful Version

Use this for a portfolio, GitHub README, or resume today.

- Designed and implemented Mercury, a production-oriented portfolio MVP for multilingual product listing and compliance workflows in cross-border commerce.
- Built a FastAPI backend workflow covering product loading, mock policy retrieval, mock LLM listing generation, deterministic compliance validation, human review gate, mock export payload, and trace recording.
- Added multi-case demo coverage for portable blender, LED desk lamp, and USB-C GaN charger cases across US/en-US and DE/de-DE.
- Modeled core data contracts including `ProductInput`, `MarketConfig`, `PolicyRule`, `GeneratedListing`, `ComplianceReport`, `HumanReview`, and `TraceEvent`.
- Implemented deterministic RuleEngine checks for required fields, forbidden terms, battery fields, electrical power fields, compatibility claim scope, safety claims, food-contact wording, unit consistency, and stale rule references.
- Added `LLMProvider` abstraction with default `MockLLMProvider` and disabled OpenAI-compatible provider skeleton to preserve a clean future replacement path.
- Added failure-path tests for unknown SKU, unsupported language, invalid market/language pair, unknown run, unknown listing, trace coverage, blocked export behavior, and stale rule references.
- Documented mock-to-production replacement paths for real LLM providers, hybrid retrieval, PostgreSQL persistence, platform adapters, review workflow, observability, evaluation, and governance.

## B. Interview Expression Version

This version is more product-oriented but still does not claim real launch or real business impact.

- Built Mercury, a production-oriented AI commerce Agent prototype that turns structured product data into multilingual listing drafts and routes risky outputs through deterministic compliance checks and human review.
- Designed the system as a controlled workflow rather than a free-form copy generator: product load, policy retrieval, listing generation, rule validation, review gate, export draft, and trace.
- Used local policy chunks and rule ids to simulate a RAG boundary, while keeping compliance decisions in a deterministic RuleEngine instead of relying only on LLM judgment.
- Refactored listing generation behind an `LLMProvider` interface so the MVP stays stable with `MockLLMProvider` today and can later connect to OpenAI-compatible, Qwen, DeepSeek, or enterprise model gateways.
- Added three representative SKU cases to prove the workflow is not hardcoded to one demo product and to cover different risk families: food-contact/battery, electrical/safety, and charger compatibility.
- Made mock boundaries explicit: no real platform API calls, no real LLM calls, no automatic publishing, and no claim of legal or platform approval.
- Added trace fields, prompt version, model info, retrieved rule references, validator summaries, and human review results to support debugging, replay, and future evaluation.

## C. Future Target Version

Use this only after the capabilities are actually implemented and evidenced.

- Evolved Mercury into a production-grade AI commerce Agent with real LLM provider routing, hybrid RAG retrieval, PostgreSQL persistence, platform adapters, review console, audit trail, and evaluation monitoring.
- Integrated versioned policy ingestion with BM25, embedding search, metadata filters, reranking, `rule_id` citations, and `policy_version` replay.
- Connected real LLM providers through a provider gateway with structured JSON output, schema validation, JSON repair, retry/fallback, prompt versioning, model tracking, latency and cost telemetry.
- Added Shopify, Google Merchant, and additional marketplace adapters with dry-run, idempotency, rate limiting, retry, export snapshots, and rollback.
- Built reviewer workflows with RBAC, approval gate, override policy, immutable audit logs, and compliance issue tracking.
- Established offline golden-case regression, hallucination tracking, compliance recall, human edit rate, cost, latency, and alerting metrics.

## Do Not Use Yet

- "上线后..."
- "服务真实客户..."
- "提升转化率 xx%..."
- "降低合规驳回率 xx%..."
- "已接入 Shopify 真实 API..."
- "已在生产环境部署..."
- "完全自动保证合规..."
