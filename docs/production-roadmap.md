# Production Roadmap

Mercury's current state is a production-oriented MVP. The roadmap below describes the path toward a production-grade AI commerce agent, not capabilities that exist today.

## Phase P1: Persistence

- Replace `InMemoryRunStore` with PostgreSQL.
- Add `run` table for request, state, product snapshot, status, timestamps.
- Add `trace` table for workflow node events.
- Add `review` table for reviewer decisions, edits, comments, and reviewer identity.
- Add `compliance_report` table for issue-level checks and validator summaries.
- Add `export_job` table for adapter draft, submission, retry, status, rollback metadata.
- Add migrations, indexes, transaction boundaries, backup/restore, and retention policy.

## Phase P2: Real Retrieval

- Build policy ingestion from approved sources.
- Chunk policies with stable chunk ids.
- Generate embeddings for semantic retrieval.
- Add BM25 for lexical retrieval.
- Add metadata filters for market, language, category, platform, risk tag, and policy version.
- Add rerank step for final ordering.
- Store `policy_version` for replay and rollback.
- Require `rule_id` citation in retrieved chunks.

## Phase P3: Real LLM

- Add provider config for mock, OpenAI-compatible, Qwen, DeepSeek, or enterprise gateway.
- Add prompt management and version registry.
- Enforce JSON schema output.
- Add JSON repair and retry.
- Add fallback provider strategy.
- Track cost, latency, token usage, provider request id, model version.
- Run regression eval before model or prompt rollout.

## Phase P4: Platform Adapter

- Add Shopify adapter.
- Add Google Merchant feed adapter.
- Add Amazon / TikTok Shop adapter when scope requires it.
- Add idempotency keys.
- Add retry and rate-limit handling.
- Add dry-run mode.
- Add rollback strategy and export snapshots.

## Phase P5: Human Review Console

- Build reviewer workflow and queues.
- Enforce approval gate.
- Add audit log for reviewer actions.
- Define override policy.
- Add reviewer comments, edits, and status transitions.
- Add reviewer SLA and escalation path if used operationally.

## Phase P6: Evaluation & Monitoring

- Build offline eval set.
- Maintain golden cases across SKU categories, markets, languages, and risk tags.
- Run regression tests for prompts, retrieval, provider changes, and rules.
- Track hallucination rate.
- Track compliance recall.
- Track human edit rate.
- Track latency.
- Track cost.
- Add alerting for failure spikes, cost spikes, and latency regressions.

## Phase P7: Security & Governance

- Add authentication.
- Add role-based access.
- Add secrets management.
- Add PII handling and redaction.
- Add immutable audit.
- Add policy change management.
- Add model/prompt release governance.
- Add data retention and deletion policy.
