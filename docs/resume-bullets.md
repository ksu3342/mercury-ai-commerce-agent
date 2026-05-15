# Mercury 简历描述草稿

本文提供两版简历描述。两版都不声称真实上线、不服务真实客户、不产生真实业务收益、不接入真实平台 API。

## 1. 保守真实版

适合简历项目经历、GitHub README、作品集页面。重点强调 PoC / 业务仿真项目和工程设计能力。

### 中文版

**Mercury 多语种商品上新与合规增长 Agent｜Portfolio PoC / 业务仿真项目**

- 设计面向跨境商品上新场景的 LLM Agent PoC 方案，覆盖商品信息结构化、规则/术语/历史文案检索、多语言 Listing 草稿生成、确定性合规预检、人工审核和 Mock 导出流程。
- 使用 FastAPI 风格 API 合同和 LangGraph 风格 workflow graph 拆分 `AnalyzeProduct`、`RetrieveContext`、`GenerateListing`、`ValidateListing`、`HumanReview`、`ExportPayload` 等节点，避免将流程控制交给模型自由发挥。
- 设计 `ProductInput`、`MarketConfig`、`PolicyRule`、`GeneratedListing`、`ComplianceReport`、`HumanReview` 等核心 schema，使模型输出能被 JSON Schema、规则引擎和人工审核共同约束。
- 构建 Mock RAG 方案，按 `rule_id`、`policy_version`、`market_id`、`category_scope`、`risk_tags` 管理规则片段，支持检索溯源和合规报告引用。
- 设计离线评估方案，包含属性完整率、合规识别 precision/recall、人工修改率、多语言质量 rubric、失败案例库和 trace 回放字段。
- 明确 PoC 边界：不接真实 Shopify / Google Merchant / Amazon API，不自动发布，不替代法务或平台审核；通过 Adapter 和 Mock payload 展示后续接入边界。

### 英文版

**Mercury Multilingual Product Listing & Compliance Agent | Portfolio PoC / Business Simulation**

- Designed a portfolio-grade LLM Agent PoC for multilingual product listing workflows, covering product normalization, policy/terminology retrieval, listing draft generation, deterministic compliance checks, human review, and mock export payloads.
- Modeled the workflow as a controlled graph with explicit nodes such as `AnalyzeProduct`, `RetrieveContext`, `GenerateListing`, `ValidateListing`, `HumanReview`, and `ExportPayload`, keeping orchestration outside the model.
- Defined core schemas including `ProductInput`, `MarketConfig`, `PolicyRule`, `GeneratedListing`, `ComplianceReport`, and `HumanReview` to constrain LLM outputs with JSON Schema, rule-based validators, and review feedback.
- Designed a mock RAG layer with `rule_id`, `policy_version`, `market_id`, `category_scope`, and `risk_tags` metadata for traceable rule retrieval and compliance reporting.
- Proposed an evaluation framework with attribute completeness, compliance precision/recall, human edit rate, multilingual quality rubric, failure case library, and run-level trace fields.
- Kept the PoC boundary explicit: no real Shopify, Google Merchant, or Amazon API integration; no automatic publishing; no claim of legal or platform approval.

## 2. 面试表达版

适合面试自我介绍、项目亮点页、口头讲解。表达更产品化，但仍不得声称真实上线或真实业务指标。

### 30 秒版本

我做了一个叫 Mercury 的多语言商品上新与合规增长 Agent。它不是简单文案生成工具，而是把商品资料结构化后，检索平台规则、品牌术语和历史优秀文案，生成英文/德文 Listing 草稿，再用 JSON Schema、规则引擎和 deterministic validators 做合规预检，最后进入人工审核并导出 Mock CSV/JSON payload。这个项目重点展示我如何把 LLM 放进可控工程系统里，而不是让模型直接决定发布内容。

### 90 秒版本

Mercury 的场景是跨境商品上新，但我真正想展示的是通用 Agent 架构能力。输入是一份不完整的商品资料，比如 Portable Blender。系统先做 ProductInput 结构化，识别电池、食品接触、EU responsible person 这类风险字段；然后 RAG 检索规则、术语和优秀文案；接着通过可替换 LLM Provider 生成 en-US 和 de-DE Listing；再由规则引擎检查必填字段、敏感词、单位、图文一致性；最后由 reviewer 做人工审核，记录修改率和失败标签。

我没有把它包装成真实上线项目。相反，我刻意保留 PoC 边界：不接真实 Shopify、Google Merchant、Amazon API，只做 Adapter 和 Shopify-like payload。这样面试时可以清楚解释：真实 API 接入是后续替换 Adapter 的问题，而项目核心是受控生成、规则校验、人审闭环和可观测评估。

### 项目亮点 bullets

- 将“多语言商品文案生成”升级为“受规则约束的内容发布 Agent”，覆盖结构化输入、RAG、生成、合规预检、人审和 Mock 导出。
- 用 workflow graph 管住 Agent 流程，避免模型直接决定下一步动作；每个节点都有明确输入、输出和失败模式。
- 用 RAG 提供上下文，但不用 RAG 替代规则引擎；合规判断由 `PolicyRule`、validator 和 `ComplianceReport` 承担。
- 用 `trace_id`、`prompt_version`、`retrieved_chunks`、`validator_result`、`human_review_result` 记录每次生成，支持回放和评估。
- 设计 failure modes 文档，覆盖 RAG 召回错误、LLM 编造规则、多语言翻译错误、单位转换错误、敏感词漏检和人工审核漏审。
- 用 Portable Blender 案例完成 5-8 分钟演示，展示英文/德文 Listing、EU blocker、人审修改和 Mock payload。

## 3. 不建议写的表述

以下说法容易被追问击穿，不建议放简历：

- 不要写：“已上线服务跨境卖家。”
- 不要写：“帮助客户提升转化率。”
- 不要写：“接入 Shopify / Amazon / Google Merchant API。”
- 不要写：“自动保证商品合规。”
- 不要写：“模型自动完成端到端发布。”
- 不要写：“真实业务中降低上新成本 XX%。”

更稳健的替代表达：

- “Portfolio PoC / 业务仿真项目。”
- “设计真实系统可迁移的 Adapter 边界。”
- “通过 Mock payload 展示发布接口形状。”
- “做合规预检和风险分级，不替代平台或法务审核。”
- “使用离线评估指标衡量草稿质量和人审修改率。”

## 4. 面试中可量化但不冒充真实业务的指标

可以说：

- “设计了属性完整率、合规 precision/recall、人工修改率等评估指标。”
- “计划用 100-200 条离线样本做回归评估。”
- “Demo 中能展示 pass、warning、blocker 三类结果。”
- “每次 run 都能回放 prompt、检索片段、规则版本和审核结果。”

不要说：

- 不要写：“真实客户修改率下降到 25%。”
- 不要写：“线上 blocker recall 达到 85%。”
- 不要写：“实际上新时间缩短到 5 分钟。”

稳妥说法：

> 这些是 PoC 验收目标和离线评估指标，不是线上业务结果。

## 5. 一句话定位

Mercury 是一个 Portfolio PoC：用跨境商品上新作为场景，展示如何把 LLM 生成能力放进可检索、可校验、可审核、可观测的工程系统中。
