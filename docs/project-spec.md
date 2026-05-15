# Mercury Project Spec

本文是 Mercury 项目的唯一事实源。后续 MVP 实现、Demo 样例、简历表达和面试答辩都以本文为准。

## 1. 项目一句话定义

Mercury 是一个 Portfolio PoC：用跨境商品上新作为业务样本，展示如何把 LLM 生成能力放进可检索、可校验、可审核、可观测的多语言内容发布前检查流程中。

边界声明：Mercury 不声称真实上线、不服务真实客户、不产生真实业务收益、不接入真实 Shopify / Google Merchant / Amazon API，不替代平台审核、法务审核或人工最终判断。

## 2. 目标用户

| 用户 | 解决的问题 | MVP 中如何体现 |
|---|---|---|
| 跨境运营 | 单 SKU 多语言上新资料整理慢、字段容易漏 | 输入 ProductInput，输出英文/德文 Listing 草稿和缺失字段 |
| 商品内容专员 | 多语言标题、卖点、详情需要术语一致 | 使用 brand_terms 和 approved_copy 约束生成 |
| 合规/质检人员 | 规则分散，人工检查不可追溯 | 输出 ComplianceReport，包含 rule_id、evidence、severity |
| 面试官 | 需要判断项目是否真实、可解释、可防击穿 | 展示状态流、schema、API、demo case、评估指标和边界 |

## 3. 核心业务问题

跨境商品上新的本质不是翻译，而是把不完整、跨语言、受规则约束的商品资料，整理成发布前可审核、可导出、可追溯的结构化内容。

Mercury 只解决 MVP 范围内的四个问题：

1. 商品资料如何结构化。
2. 生成时如何引用规则、术语和样例。
3. 输出如何被确定性规则检查。
4. 结果如何进入人工审核和评估闭环。

## 4. 输入 / 输出

### 输入

核心输入是 `ProductInput`：

- `sku`
- `source_language`
- `title`
- `description`
- `brand`
- `category_hint`
- `target_markets`
- `target_languages`
- `attributes`
- `image_assets`
- `regulatory_tags`

最小 Demo SKU 固定为：

```text
MRC-BLEND-450-WH
```

### 输出

MVP 输出包括：

- `product_profile`：结构化商品画像、风险标签、缺失字段。
- `GeneratedListing[]`：英文和德文 Listing 草稿。
- `ComplianceReport[]`：每个 Listing 的合规预检报告。
- `HumanReview`：人工审核决定、修改记录、修改率。
- Mock export：CSV、JSON、Shopify-like payload。
- Run trace：`trace_id`、`prompt_version`、`retrieved_chunks`、`validator_result`、`human_review_result`。

## 5. MVP 范围

MVP 必做：

- 单商品输入，使用 Portable Blender / 便携榨汁杯案例。
- 目标市场：`US`、`DE`。
- 目标语言：`en-US`、`de-DE`。
- 本地 Mock RAG：`policy_chunks`、`brand_terms`、`approved_copy`。
- LLMProvider 抽象：可用 mock 或任意兼容模型。
- 结构化输出：Listing 和报告都以 JSON 表达。
- 规则引擎：至少覆盖 EU 负责人字段、电池字段、食品接触表达、禁用健康功效声明、品牌词不翻译。
- 人工审核：支持 `approved`、`changes_requested`、`rejected`。
- Mock 导出：CSV、JSON、Shopify-like payload。
- Run 查询：用 `run_id` 汇总状态、trace、生成、校验、审核和导出结果。

## 6. 非目标范围

MVP 不做：

- 不接真实 Shopify / Google Merchant / Amazon API。
- 不自动发布到任何真实平台。
- 不处理真实订单、支付、客户 PII。
- 不做模型微调。
- 不做复杂 RBAC、SSO、多租户权限。
- 不做完整多模态视觉理解；只使用图片 URL、alt text、Mock OCR 文本。
- 不做大规模向量库和分布式任务队列。
- 不给法律意义上的合规结论。

## 7. 核心流程

```text
ProductInput
  -> AnalyzeProduct
  -> RetrieveContext
  -> GenerateListing
  -> ValidateListing
  -> HumanReview
  -> ExportPayload
  -> GetRun
```

每一步必须能回答：

- 输入是什么。
- 输出是什么。
- 调用了哪个工具。
- 失败后怎么处理。
- trace 中记录什么。

## 8. Agent 状态流

```text
RECEIVED
  -> ANALYZING
  -> CONTEXT_READY
  -> GENERATING
  -> GENERATED
  -> CHECKING
  -> READY_FOR_REVIEW | REVIEW_REQUIRED
  -> HUMAN_REVIEWING
  -> APPROVED | REVISION_REQUESTED | REJECTED
  -> EXPORTED | ARCHIVED
```

状态流解决的问题：避免让模型自由决定流程。LLM 只在受控节点内生成或解释，状态迁移由 workflow graph 控制。

## 9. 工具列表

| 工具 | 解决的问题 | MVP 输入 | MVP 输出 |
|---|---|---|---|
| `ProductAnalyzer` | 结构化商品资料，识别缺失字段和风险标签 | ProductInput、MarketConfig | product_profile |
| `PolicyRetriever` | 找到适用规则 | market、category、risk_tags | policy chunks |
| `TerminologyRetriever` | 保证品牌和术语一致 | brand、category、language | brand_terms |
| `ApprovedCopyRetriever` | 提供写作风格参考 | category、market、language | approved_copy chunks |
| `LLMProvider.generate_json` | 生成结构化 Listing 或解释 | prompt、schema、context | JSON output |
| `JsonSchemaValidator` | 检查输出结构 | JSON output、schema | pass/fail |
| `RuleEngine` | 执行确定性合规规则 | listing、PolicyRule、MarketConfig | ComplianceReport checks |
| `UnitValidator` | 检查数值和单位一致 | listing attributes | pass/warning/fail |
| `SensitiveTermChecker` | 检查高风险表达 | title、bullets、description、claims | matched terms |
| `ImageTextChecker` | 检查 OCR 与属性冲突 | image_assets、attributes | consistency warnings |
| `HumanReviewRecorder` | 记录人工决定和修改 | edited_listing、decision | HumanReview |
| `ExportAdapter` | 生成 Mock 导出 | approved listing | CSV / JSON / Shopify-like payload |
| `RunRepository` | 汇总 run 状态和 trace | run_id | run detail |

## 10. LLM 负责什么

LLM 负责不确定性较高的语言任务：

- 从非结构化描述中提取候选结构，但不能编造事实。
- 根据已知事实生成英文和德文 Listing 草稿。
- 根据规则检查结果生成面向 reviewer 的解释。
- 修复 JSON 格式错误，但不能改变业务含义。

LLM 不负责：

- 判断最终合规。
- 决定是否导出。
- 创造规则。
- 填写不存在的认证、材质、功效、平台通过结论。

## 11. 规则引擎负责什么

规则引擎负责必须稳定、可复现的判断：

- 必填字段是否存在。
- `rule_id` 是否存在于当前 `policy_version`。
- 标题长度是否超限。
- 禁用词或高风险声明是否出现。
- 单位和数值是否一致。
- blocker 是否清零。

规则引擎输出 `validator_result` 和 `ComplianceReport.checks`。它不负责生成自然语言文案。

## 12. RAG 负责什么

RAG 负责提供可追溯上下文：

- 平台/市场规则片段。
- 品牌术语。
- 历史优秀文案样例。
- 失败案例参考。

RAG 不替代规则引擎。RAG 只能提供“可参考的知识”，不能决定“是否违规”。所有合规结论必须落到 `PolicyRule`、`RuleEngine` 和 `ComplianceReport`。

## 13. 人工审核负责什么

人工审核负责发布前责任边界：

- 判断 Listing 是否可接受。
- 修改标题、卖点、详情或属性。
- 对 blocker / warning 做确认。
- 标记失败类型。
- 产生 `human_review_result`，用于评估人工修改率和失败案例。

MVP 中 blocker 未清零时，不允许 Mock export 标记为 approved。

## 14. 可观测字段

每次 run 必须记录：

| 字段 | 用途 |
|---|---|
| `run_id` | 串联一次端到端流程 |
| `trace_id` | 回放单次执行链路 |
| `prompt_version` | 比较 prompt 变更影响 |
| `policy_version` | 回溯规则版本 |
| `retrieved_chunks` | 说明 RAG 依据 |
| `validator_result` | 说明机器校验结果 |
| `human_review_result` | 说明人工审核反馈 |
| `model_info` | 记录 provider、model、temperature |
| `status_transition` | 检查 Agent 状态迁移 |

## 15. 评估指标

MVP 使用离线和演示指标，不声称线上业务结果。

| 指标 | 数据来源 | 说明 |
|---|---|---|
| 属性完整率 | ProductInput、MarketConfig、GeneratedListing.attributes | 必填属性是否填写或显式暴露缺失 |
| 合规 precision / recall | gold policy issue、ComplianceReport.checks | 合规预检是否误报或漏报 |
| 人工修改率 | GeneratedListing、HumanReview.edited_listing | reviewer 改了多少 |
| 多语言质量 rubric | HumanReview 或人工评分表 | 语义保真、术语一致、本地化、合规语气 |
| JSON 失败率 | LLM output、JsonSchemaValidator | 结构化输出稳定性 |
| Trace 完整率 | RunRepository | 是否记录必要可观测字段 |
| 失败案例回归通过率 | failure_cases、eval samples | 历史错误是否复现和修复 |

## 16. Canonical Demo Rule IDs

MVP demo 使用以下规则 ID：

| rule_id | 用途 |
|---|---|
| `EU_GPSR_RESPONSIBLE_PERSON_REQUIRED` | DE/EU 市场负责人字段 blocker |
| `US_UNSUPPORTED_HEALTH_CLAIM` | US 市场不支持健康/医疗功效声明 blocker |
| `FOOD_CONTACT_MATERIAL_DISCLOSURE` | 食品接触材料表达 warning |
| `BATTERY_CAPACITY_FIELD_REQUIRED` | 电池容量和充电类型字段 warning |
| `BRAND_TERM_DO_NOT_TRANSLATE` | 品牌词不得翻译 |
| `TITLE_LENGTH_BY_MARKET` | 标题长度按市场检查 |

Canonical policy version：

```text
demo-policy-2026-05
```

## 17. 面试口径边界

可以说：

- Mercury 是 Portfolio PoC / 业务仿真项目。
- 它展示了受控 Agent 流程、RAG 溯源、规则校验、人审闭环和评估方案。
- 它通过 Mock payload 展示未来 Adapter 接入边界。
- 它用离线评估指标定义质量目标。

不要说：

- 不要说：已上线。
- 不要说：有真实客户使用。
- 不要说：接入了真实 Shopify / Google Merchant / Amazon API。
- 不要说：产生了真实业务收益。
- 不要说：自动保证所有平台合规。
- 不要说：替代人工审核、平台审核或法务审核。
