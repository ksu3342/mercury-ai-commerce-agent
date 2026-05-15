# Mercury MVP Scope

本文定义 Mercury 第一版 MVP 的边界。核心目标是做出一个面试可解释、可演示、可防击穿的 Portfolio PoC，不声称真实上线、不服务真实客户、不产生真实业务收益、不接真实平台 API。

## 1. MVP 定位

Mercury MVP 只验证一条最小闭环：

```text
ProductInput -> 商品结构化 -> RAG 上下文检索 -> 多语言 Listing 生成 -> 合规预检 -> 人工审核 -> Mock 导出 -> Run 追踪
```

它解决的问题不是“自动经营跨境电商店铺”，而是证明一个 LLM Agent 系统如何在受规则约束的内容发布场景中控制风险。

## 2. MVP 必做功能

| 功能 | 解决的问题 | 最小实现 | 验收方式 |
|---|---|---|---|
| 商品录入 | 输入不统一，无法直接生成 | 支持 `ProductInput` JSON 或表单录入 | 能提交 Portable Blender 样例 |
| 商品结构化 | 缺失字段和风险标签需要显式暴露 | 输出 `product_profile`、`missing_attributes`、`detected_risk_tags` | 能识别 `battery`、`food_contact`、EU 必填字段缺失 |
| Mock RAG 检索 | 生成需要规则、术语和样例约束 | 从本地 `policy_chunks`、`brand_terms`、`approved_copy` 返回 top_k | 每次生成记录 `retrieved_chunks` 和 `rule_id` |
| 多语言 Listing 生成 | 需要英文和德文草稿 | 通过 `LLMProvider` 抽象输出结构化 `GeneratedListing` | 生成 en-US、de-DE 标题、卖点、详情 |
| 合规预检 | 不能直接相信生成内容 | JSON Schema + deterministic validators + rule engine | 输出 `ComplianceReport`，含 blocker/warning |
| 人工审核 | 控制发布风险，沉淀评估数据 | 支持 approved / changes_requested / rejected | 记录 `human_review_result` 和修改率 |
| Mock 导出 | 展示发布边界和 Adapter 思路 | 导出 CSV、JSON、Shopify-like payload | 能在 demo-case 中展示 payload |
| Run 查询 | 面试时回放完整链路 | `GET /runs/{run_id}` 汇总状态、trace、结果 | 能查到 `trace_id`、`prompt_version`、`validator_result` |
| 失败案例记录 | 错误要可复现、可修复 | 将 rejected 或 blocker 样本写入 failure case | 至少展示 1 个失败案例 |

## 3. 暂不实现功能

| 暂不实现 | 原因 | 后续何时做 |
|---|---|---|
| 真实 Shopify / Google Merchant / Amazon API | 会把重点从 Agent 核心链路转移到账户、鉴权、限流、字段兼容 | MVP 指标稳定后再做 Adapter 实接 |
| 模型微调 | 当前问题主要是流程、上下文、结构化输出和规则校验，不是模型参数不足 | 当有足够人工审核样本和稳定错误模式后再评估 |
| 复杂权限系统 | PoC 只需要 reviewer/admin 概念，不需要 RBAC、SSO、审计权限矩阵 | 多用户协作 Demo 或准生产环境再做 |
| 自动发布 | 发布动作有业务和法律风险，PoC 只导出 mock payload | 有真实权限、回滚、审计和人工批准后再考虑 |
| 完整多模态识别 | v1 可用图片 URL、alt text、Mock OCR 文本做一致性检查 | 需要展示图片理解能力时接 VL 模型 |
| 大规模向量库 | v1 规则和样例规模小，Mock retriever / FAISS 足够 | 文档规模扩大到万级 chunk 后再接 Milvus |
| 分布式任务队列 | MVP 可以同步执行或本地异步，重点是状态清楚 | 多 SKU 批处理或长任务需要时再接 Celery/Redis |
| 真实法律合规结论 | 系统只做合规预检和风险提示 | 生产化需法务、平台政策和人工复核共同定义 |

## 4. 为什么不接真实 Shopify / Google Merchant / Amazon API

不接真实 API 是有意控制 MVP 边界，不是回避工程问题。

真实平台接入会引入：

- 账号和权限申请。
- OAuth、token 刷新、限流、重试。
- 平台字段版本差异。
- 真实商品和客户数据安全。
- 平台审核结果不可控。

这些问题真实存在，但它们不是当前 PoC 的最小证明点。当前要证明的是：

- Agent 状态机能否稳定串起流程。
- 模型输出能否被 schema 和规则约束。
- 合规风险能否被分级、解释和人审。
- 每次 run 能否被追踪和评估。

因此 MVP 用 Adapter 接口和 Mock payload 保留真实接入边界。后续实接 API 时，只替换 Adapter，不改变核心 workflow。

## 5. 为什么不做模型微调

MVP 阶段不做微调，原因有三点：

1. 数据不足：没有足够真实人工审核样本，微调容易过拟合少量样例。
2. 问题未分型：当前更需要先区分是检索错、prompt 错、规则错还是模型表达错。
3. 成本不匹配：结构化输出、RAG、规则引擎和人审反馈能先解决大部分可解释问题。

更合理的路线是：

```text
先做 prompt + schema + validators -> 收集失败案例 -> 形成稳定错误分布 -> 再判断是否需要微调
```

如果后续微调，目标也不是“让模型懂所有规则”，而是优化术语一致性、文案风格和结构化输出稳定性。合规判断仍然不能交给微调模型独自承担。

## 6. 为什么不做复杂权限系统

MVP 只模拟两类角色：

- `operator`：提交商品、查看生成结果。
- `reviewer`：审核、编辑、批准或驳回。

不做复杂权限系统的原因：

- 当前没有真实多租户和真实客户数据。
- 权限系统会增加实现成本，但不提升 Agent 核心能力证明。
- 面试阶段只需要说明生产化时会补充 RBAC、审计日志、字段级权限和 SSO。

MVP 保留 `reviewer_id`、`reviewed_at`、`decision` 这些字段，足够展示审核责任链。

## 7. MVP 验收标准

MVP 完成后，必须能演示以下内容：

| 验收项 | 标准 |
|---|---|
| 端到端流程 | Portable Blender 样例能完成 analyze -> generate -> check -> review -> export |
| 多语言输出 | 至少生成 en-US 和 de-DE 两个 Listing |
| 规则溯源 | 合规报告能显示 `rule_id`、`policy_version`、`retrieved_chunks` |
| 风险识别 | EU responsible_person 缺失能被标为 blocker |
| 人审闭环 | 能展示人工修改记录和 `estimated_edit_rate` |
| Mock 导出 | 能输出 CSV 行和 Shopify-like JSON payload |
| 可观测 | `GET /runs/{run_id}` 能展示 `trace_id`、`prompt_version`、`validator_result`、`human_review_result` |
| 评估材料 | 至少有 1 个 pass、1 个 warning、1 个 blocker 案例 |
| 边界说明 | 文档明确说明不接真实 API、不自动发布、不替代法务 |

## 8. 后续生产化扩展路线

生产化扩展不是 MVP 必须完成的功能，只作为面试追问时的路线图。

### Phase 1: PoC Demo

- Mock retriever / FAISS。
- Mock LLMProvider。
- 本地规则包。
- CSV / JSON / Shopify-like mock export。
- 人工审核和失败案例库。

### Phase 2: Engineering Hardening

- PostgreSQL 持久化 run、listing、report、review。
- 后台任务队列处理批量 SKU。
- OpenTelemetry trace 和基础 metrics。
- Prompt/version 管理。
- 离线评测集和回归测试。

### Phase 3: Adapter Real Integration

- Shopify GraphQL Adapter。
- Google Merchant feed Adapter。
- Amazon flat file / SP-API Adapter 评估。
- API 错误码、限流、重试和幂等。

### Phase 4: Governance

- RBAC、SSO、审计日志。
- 规则变更审批。
- 高风险类目强制人工审核。
- 模型和 prompt 版本灰度。

### Phase 5: Optimization

- Hybrid retrieval + rerank。
- 基于人工审核数据优化 prompt。
- 必要时做轻量微调或偏好优化。
- 成本、延迟、通过率和人工修改率看板。

## 9. 面试防守口径

推荐说法：

> Mercury MVP 不追求假装生产上线，而是把真实系统里最容易出问题的部分先做清楚：输入结构化、规则检索、受控生成、确定性校验、人工审核和可观测评估。真实平台 API 和复杂权限属于后续生产化扩展，不是第一版证明核心能力的前提。
