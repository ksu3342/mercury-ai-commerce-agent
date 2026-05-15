# Mercury 多语种商品上新与合规增长 Agent

Mercury 是一个 Portfolio PoC / Business Simulation Project，用于展示多语言内容生成、规则校验、人工审核和可观测评估的 Agent 系统设计。

## 当前阶段

当前项目包含设计文档和最小样例数据集，尚未包含后端业务代码、前端 Demo 或真实平台集成。

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
```

## 边界说明

- 不包含真实 Shopify、Google Merchant、Amazon 等平台 API 接入。
- 不包含真实客户数据。
- 不声明真实业务收益。

## 后续计划

- 后端 MVP
- 前端 Demo
- 面试讲稿
