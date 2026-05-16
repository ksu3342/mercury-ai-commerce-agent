# Mercury 多语种商品上新与合规增长 Agent

Mercury 是一个 Portfolio PoC / Business Simulation Project，用于展示多语言内容生成、规则校验、人工审核和可观测评估的 Agent 系统设计。

## 当前阶段

当前项目已经完成：

- 设计文档；
- `data/demo` 最小样例数据集；
- `backend` 4A MVP，用 FastAPI 跑通 demo workflow、mock retrieval、mock listing、deterministic rule engine、human review 和 run trace。

当前暂未包含：

- 前端 Demo；
- 真实 LLM 接入；
- 真实向量库；
- 真实 Shopify、Google Merchant、Amazon 等平台 API 接入。

## 目录结构

```text
docs/
  architecture.md
  data-schema.md
  api-contract.md
  evaluation-plan.md
  interview-defense.md
  mvp-scope.md
  demo-case.md
  failure-modes.md
  rag-design.md
  prompt-strategy.md
  resume-bullets.md
  project-spec.md
  consistency-audit.md

data/
  demo/
    product_input.json
    market_configs.json
    policy_rules.jsonl
    policy_chunks.jsonl
    brand_terms.json
    approved_copy.jsonl
    expected_generated_listings.json
    expected_compliance_report.json
    human_review.json
    export.csv
    shopify_like_payload.json
    run_record.json

backend/
  app/
  tests/
  requirements.txt
  README.md
```

## 边界说明

- 不包含真实 Shopify、Google Merchant、Amazon 等平台 API 接入。
- 不包含真实 LLM 或真实向量库接入。
- 不包含真实客户数据。
- 不声明真实业务收益。

## 后续计划

- 前端 Demo
- 后端 MVP 下一阶段
- 面试讲稿
