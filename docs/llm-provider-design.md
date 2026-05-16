# LLM Provider Design

## Why 4D Only Adds Provider Abstraction

Phase 4D intentionally adds an `LLMProvider` boundary without calling a real model. The goal is to prepare the architecture for production evolution while keeping the current MVP deterministic, cheap, offline, and testable.

Current status: production-oriented MVP.

Current non-status: production system.

## Why Not Call A Real LLM Now

A real LLM would add output instability, invalid JSON, hallucination risk, provider latency, provider cost, prompt drift, and security concerns. Those risks should be introduced only after the workflow, schemas, validation, review gate, trace, and eval path are stable.

No evidence indicates that this MVP currently calls OpenAI, Qwen, DeepSeek, or any online LLM.

## Interface

`LLMProvider.generate_listing_json(...)` accepts:

- `product`;
- `market_config`;
- `retrieved_chunks`;
- `prompt_version`;
- optional `generation_config`.

It returns `LLMGenerationResult`:

- `payload: dict`;
- `model_info: dict`;
- `prompt_version: str`;
- `raw_output: Optional[str]`;
- `validation_errors: list`.

The workflow does not depend on a specific model vendor.

## Current Default: MockLLMProvider

`MockLLMProvider` reads `expected_generated_listings.json` for the requested SKU and market. It emits stable JSON, `model_info.provider = "mock_llm"`, and a `prompt_version`.

This makes demo output deterministic and keeps tests independent from network, API keys, model availability, and provider pricing.

## OpenAI-Compatible Provider Skeleton

`OpenAICompatibleProvider` captures the future adapter shape:

- `base_url`;
- `api_key`;
- `model`;
- timeout;
- enabled flag.

It is intentionally disabled and raises `NotImplementedError`. It must not read real environment variables or send network requests in this MVP.

## Structured Output Strategy

Future real providers should request structured JSON output and then validate it locally. The provider may ask the model for JSON, but the system must not trust model formatting blindly.

Required future steps:

- define JSON schema for `GeneratedListing`;
- validate required fields;
- reject missing high-risk fields or mark them as missing;
- convert output into typed models only after validation.

## JSON Schema Validation And Repair

Current lightweight helpers:

- `try_parse_json`;
- `repair_common_json_errors`;
- `validate_generated_listing_payload`.

These are not a full parser. They only cover common simple issues such as single quotes and trailing commas. Production should add schema validation, strict error reporting, retry prompts, and possibly a repair model or deterministic repair pipeline.

## Prompt Version

Every generated listing carries `prompt_version`. This is needed for replay, debugging, evaluation, and rollback. If prompt behavior changes, the system should be able to compare outputs by prompt version.

## Model Info

Every provider output carries `model_info`, including provider and model name. Production should also record model version, temperature, output mode, token usage, latency, and provider request id.

## Hallucination Defense

The prompt instructs the model not to invent:

- certifications;
- materials;
- efficacy;
- safety proof;
- platform policy;
- legal status.

Missing fields must be marked as missing. Retrieved `rule_id` values must be cited where relevant. The RuleEngine still checks the result after generation.

## Cost And Latency Control

Production provider work should add:

- max token budget;
- timeout;
- retry limit;
- fallback provider;
- caching where safe;
- cost logging;
- latency metrics;
- alerts for cost spikes or slow runs.

## Output Safety

Generated output must remain a draft until validators and human review allow further action. The LLM provider must not control workflow transitions or platform export.

## Prompt Drift

Prompt changes can silently change model behavior. Production should use prompt registry, prompt versioning, golden-case regression tests, staged rollout, and rollback.

## Evaluation Regression

Every provider change should run against offline golden cases:

- blender food-contact and battery risk;
- LED lamp electrical and safety-claim risk;
- charger voltage and compatibility-claim risk;
- unknown SKU and invalid locale failures;
- stale rule reference warnings.

Metrics should include schema pass rate, compliance recall, hallucination rate, human edit rate, latency, and cost.

## Why RuleEngine Remains Necessary

LLMs are probabilistic. Compliance checks need deterministic, reproducible gates. The RuleEngine catches required field misses, forbidden claims, broad compatibility claims, absolute safety claims, stale rule references, and market/language constraints independently of the model.

## Current Non-Claims

This MVP cannot claim:

- real LLM integration;
- production model routing;
- model cost tracking;
- model latency SLOs;
- model safety certification;
- fully automated compliance approval.

## Future Production Steps

1. Add provider config that can select mock, OpenAI-compatible, Qwen, DeepSeek, or enterprise gateway.
2. Add strict JSON schema for `GeneratedListing`.
3. Add retry and fallback around invalid output.
4. Add token, cost, latency, and request-id telemetry.
5. Add prompt registry and model version tracking.
6. Add offline eval gates before provider rollout.
7. Keep human review and RuleEngine gates after real model integration.
