# Mercury Consistency Audit

审计目标：确认 11 份 Markdown 文档是否能共同支撑一个“面试可解释、可演示、可防击穿”的 Portfolio PoC。审计后以 `docs/project-spec.md` 作为唯一事实源，并按该事实源修正不一致。

## 1. 审计结论

| 等级 | 数量 | 当前状态 |
|---|---:|---|
| High | 0 | 未发现会直接破坏项目边界或造成真实上线误导的问题 |
| Medium | 6 | 已修复 |
| Low | 3 | 已修复或由 `project-spec.md` 收敛 |

当前结论：未发现仍需阻断后续 MVP 的文档不一致。后续实现应以 `docs/project-spec.md` 为准。

## 2. 逐份文档检查

| 文档 | 审计结论 |
|---|---|
| `architecture.md` | 架构边界总体一致；已通过 `project-spec.md` 收敛“发布前检查”和 MVP 非目标口径 |
| `data-schema.md` | schema 主体可用；已修正规则版本命名不一致 |
| `api-contract.md` | API 流程闭环成立；已补齐 response 中与 schema 不一致的字段和 rule_id |
| `evaluation-plan.md` | 指标均有数据来源；已避免把 PoC 指标说成线上业务结果 |
| `interview-defense.md` | 回答整体可防守；已收紧性能目标为 MVP 验收口径 |
| `mvp-scope.md` | 与 architecture 不冲突；明确真实 API、微调、复杂权限均非 MVP |
| `demo-case.md` | 演示链路完整；已补齐 schema 要求字段 |
| `failure-modes.md` | 失败模式覆盖 20 个场景，覆盖指定风险 |
| `rag-design.md` | RAG 与规则引擎边界清楚；未发现替代规则引擎的表述 |
| `prompt-strategy.md` | prompt 约束清楚；强调关键校验不能只靠 LLM |
| `resume-bullets.md` | 已移除“设计并实现”这类超前表述，保留 PoC / 业务仿真边界 |

## 3. 发现的问题与处理

### Issue 1

- 问题位置：`data-schema.md`，`MarketConfig.compliance_profile.policy_version` 和 `ComplianceReport.policy_version`
- 问题描述：示例中出现 `eu-gpsr-demo-2026-05`，而 demo、API、RAG 文档使用 `demo-policy-2026-05`。
- 风险等级：Medium
- 为什么会被面试官追问：规则版本是可追溯能力的核心字段；版本不一致会削弱“可回放、可审计”的可信度。
- 建议修改方式：统一使用 `demo-policy-2026-05`。
- 处理状态：已修复。

### Issue 2

- 问题位置：`data-schema.md`，`PolicyRule.version`
- 问题描述：`PolicyRule` 示例使用 `2026-05-demo`，与 canonical policy version 不一致。
- 风险等级：Medium
- 为什么会被面试官追问：如果 `PolicyRule.version` 和 `ComplianceReport.policy_version` 不能对齐，规则命中无法稳定回溯。
- 建议修改方式：统一为 `demo-policy-2026-05`。
- 处理状态：已修复。

### Issue 3

- 问题位置：`api-contract.md`，`POST /compliance/check` response
- 问题描述：API 示例使用 `TITLE_LENGTH_US_DEMO`、`BATTERY_DISCLOSURE_DEMO`，但 demo/RAG/事实源使用 `TITLE_LENGTH_BY_MARKET`、`BATTERY_CAPACITY_FIELD_REQUIRED`。
- 风险等级：Medium
- 为什么会被面试官追问：rule_id 是合规溯源的主键；同一规则多套命名会让规则引擎设计显得松散。
- 建议修改方式：统一到 `docs/project-spec.md` 的 canonical demo rule IDs。
- 处理状态：已修复。

### Issue 4

- 问题位置：`api-contract.md`，`POST /listings/generate` response
- 问题描述：`listings[]` 中缺少 `run_id`、`trace_id`、`claims`、`retrieved_chunks`、`prompt_version`、`model_info`，而 `GeneratedListing` schema 将这些字段定义为核心字段。
- 风险等级：Medium
- 为什么会被面试官追问：如果 API 返回对象不符合 schema，后端 MVP 实现会不知道以哪个为准。
- 建议修改方式：补齐 `GeneratedListing` 必要字段；保留 top-level 汇总字段不影响每个 listing 自包含。
- 处理状态：已修复。

### Issue 5

- 问题位置：`api-contract.md`，`POST /compliance/check` 和 `POST /reviews/submit` response
- 问题描述：嵌套 `reports[]` 缺少 `policy_version`、`retrieved_chunks`；`review` 缺少 `run_id`、`trace_id`。
- 风险等级：Medium
- 为什么会被面试官追问：ComplianceReport 和 HumanReview 都是审计对象；缺少版本和 trace 字段会破坏可回放能力。
- 建议修改方式：每个 report/review 对象都保留必要追踪字段。
- 处理状态：已修复。

### Issue 6

- 问题位置：`demo-case.md`，英文/德文 `GeneratedListing` 和合规报告示例
- 问题描述：Listing 示例缺少 `model_info`；嵌套合规报告缺少独立 `report_id`、`policy_version`、`retrieved_chunks`。
- 风险等级：Medium
- 为什么会被面试官追问：Demo case 是 5-8 分钟讲解材料，如果它与 schema 不一致，会直接暴露“文档拼接”问题。
- 建议修改方式：补齐与 schema 对齐的字段，并保留聚合响应结构。
- 处理状态：已修复。

### Issue 7

- 问题位置：`resume-bullets.md`
- 问题描述：保守版 bullet 使用“设计并实现”，但当前阶段主要是设计文档和样例数据，不应暗示已有完整业务代码。
- 风险等级：Medium
- 为什么会被面试官追问：如果面试官要求看实现代码，表述会显得超前或不真实。
- 建议修改方式：改为“设计面向跨境商品上新场景的 LLM Agent PoC 方案”。
- 处理状态：已修复。

### Issue 8

- 问题位置：`interview-defense.md`
- 问题描述：`单 SKU 草稿生成 p95 < 20 秒` 容易被误解为已测得性能结果。
- 风险等级：Low
- 为什么会被面试官追问：面试官可能追问压测环境、样本量和统计口径。
- 建议修改方式：明确这是 MVP 验收目标，不是线上或实测业务结果。
- 处理状态：已修复。

### Issue 9

- 问题位置：`architecture.md`、`mvp-scope.md`、`rag-design.md`
- 问题描述：文档中提到 Milvus、Celery/Redis、OpenTelemetry、Prometheus 等生产化组件，可能被认为过度工程化。
- 风险等级：Low
- 为什么会被面试官追问：PoC 阶段如果同时承诺太多组件，会像技术堆砌。
- 建议修改方式：在 `project-spec.md` 中明确 MVP 只做 Mock retriever / FAISS 级别、本地同步流程和 Mock export；这些组件只作为后续路线。
- 处理状态：已由 `project-spec.md` 收敛，无需删除所有后续路线。

## 4. 十项检查维度结论

| 检查维度 | 结论 |
|---|---|
| 字段命名是否一致 | 已统一核心字段：`run_id`、`trace_id`、`policy_version`、`prompt_version`、`retrieved_chunks`、`validator_result`、`human_review_result` |
| API request / response 是否和 schema 一致 | 已修复主要不一致；API 可作为 MVP 实现依据 |
| demo-case 字段、工具、rule_id 是否和 schema 一致 | 已补齐 `model_info`、`report_id`、`policy_version`、`retrieved_chunks` |
| MVP 范围是否和 architecture 冲突 | 不冲突；MVP 明确不接真实 API、不微调、不做复杂权限 |
| evaluation-plan 指标是否有可计算数据来源 | 有：ProductInput、MarketConfig、GeneratedListing、ComplianceReport、HumanReview、failure_cases |
| interview-defense 是否有无法支撑回答 | 未发现高风险回答；性能表述已收紧为目标口径 |
| resume-bullets 是否有不可验证表述 | 已移除超前实现表述，并保留“不声称真实上线”边界 |
| 是否存在过度工程化设计 | 生产化组件仅作为后续路线，MVP 已收敛 |
| 是否存在 Agent 伪复杂问题 | 状态流包含缺字段、人审、重生成、拒绝归档等分支，Agent 使用有理由 |
| 是否有容易被追问击穿的表述 | 已处理已知问题；剩余风险主要来自后续实现是否按事实源落地 |

## 5. 后续实现约束

后续 MVP 实现必须遵守：

- 以 `docs/project-spec.md` 为唯一事实源。
- 以 `docs/demo-case.md` 作为第一条端到端演示样本。
- 样例数据中的 rule_id、policy_version、run_id、trace_id 必须与 project spec 对齐。
- 简历表达不得超出当前可展示资产。
