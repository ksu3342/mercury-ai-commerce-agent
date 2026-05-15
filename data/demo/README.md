# Mercury Minimal Demo Dataset

This dataset is the smallest end-to-end sample for the Mercury Portfolio PoC.

It is based on:

- `docs/project-spec.md`
- `docs/demo-case.md`

Boundary:

- No real Shopify, Google Merchant, or Amazon API data.
- No real customer data.
- No real business metrics.
- All payloads are mock/demo artifacts for MVP implementation and interview explanation.

## Files

| File | Purpose |
|---|---|
| `product_input.json` | Original Portable Blender ProductInput |
| `market_configs.json` | US and DE market config |
| `policy_rules.jsonl` | Canonical demo policy rules |
| `policy_chunks.jsonl` | RAG retrievable policy chunks |
| `brand_terms.json` | Protected brand/term rules |
| `approved_copy.jsonl` | Minimal approved copy examples |
| `expected_generated_listings.json` | Expected en-US and de-DE listing drafts |
| `expected_compliance_report.json` | Expected compliance check output |
| `human_review.json` | Human review edit record |
| `export.csv` | Mock CSV export |
| `shopify_like_payload.json` | Mock Shopify-like JSON payload |
| `run_record.json` | End-to-end run summary for `GET /runs/{run_id}` |

## Canonical IDs

- `run_id`: `run_demo_blender_001`
- `trace_id`: `trc_demo_blender_001`
- `policy_version`: `demo-policy-2026-05`
- `prompt_version`: `listing_generator_v1.0.0`
- `sku`: `MRC-BLEND-450-WH`
