# Mercury Failure Modes

本文列出 Mercury PoC 可能失败的场景。目标不是证明系统不会失败，而是提前说明如何检测、隔离、缓解和回归。

## 1. 失败模式总览

| # | 失败场景 | 失败描述 | 发生原因 | 影响 | 检测方式 | 缓解策略 |
|---:|---|---|---|---|---|---|
| 1 | RAG 召回错误 | 检索到不适用市场或不适用类目的规则 | metadata 过滤不足、query 过宽、chunk 粒度不合理 | 生成引用错误规则，合规报告误报 | 抽查 `retrieved_chunks`；检查 `market_id`、`category_scope`、`rule_id` | 强制 metadata filter；提高 rule chunk 权重；失败案例标记 `retrieval_noise` |
| 2 | RAG 召回缺失 | 应检索到的关键规则没有返回 | query 未包含风险标签；top_k 太小；embedding 不适合短规则 | 漏掉 blocker，例如 EU 负责人字段 | gold policy issue 中有规则但 `retrieved_chunks` 无对应 `rule_id` | rule_id 关键词召回兜底；按 risk tag 直接加载必查规则；调大 top_k |
| 3 | LLM 编造规则 | 模型生成“平台禁止某材质”等不存在规则 | prompt 没要求只引用已检索规则；上下文缺失时模型补全 | 合规报告失真，面试容易被击穿 | 检查输出 rule_id 是否存在于 `PolicyRule` 表 | 合规解释 prompt 只允许引用已知 rule_id；未知规则输出 `insufficient_evidence` |
| 4 | LLM 编造商品属性 | 输入没有防水等级，模型生成 IPX7 | 模型根据相似商品模式补全事实 | 发布内容虚假，合规风险高 | 比对 generated attributes 与 ProductInput source fields | facts whitelist；事实字段缺失时只能输出 null 或 `needs_human_input` |
| 5 | 多语言翻译错误 | 德文 Listing 把品牌名 Mori 翻译或改写 | 术语库未命中；prompt 未约束不可翻译词 | 品牌一致性下降，内容不可用 | terminology validator 检查品牌词和保留词 | brand_terms 强制注入；品牌词 exact match validator |
| 6 | 多语言语气不合规 | 文案使用 “100% safe”、“guaranteed healthy” | 生成时追求营销效果，未限制绝对化表达 | 触发敏感声明或平台拒登 | sensitive term checker；claim classifier | 禁用词表 + claim severity；高风险声明进入 blocker |
| 7 | 单位转换错误 | 450 ml 被错误写成 450 oz 或 0.45 ml | 模型自由换算；市场单位规则不明确 | 核心规格错误，严重误导 | unit validator 比对数值和单位 | 数值字段禁止 LLM 自行换算；单位转换由 deterministic function |
| 8 | 图片与文本不一致 | 图片 OCR 显示 600ml，属性为 450ml | 图片来自旧款或用户上传错误 | Listing 与图片冲突，审核风险 | image-text consistency checker 比对 OCR 和 attributes | 标记 warning；要求人工确认图片或属性 |
| 9 | 敏感词漏检 | 文案出现治疗、减肥或绝对安全暗示但未命中词表 | 敏感表达是语义变体，词表覆盖不足 | 合规 recall 下降 | 人工审核标记；离线 gold set FN 统计 | 增加语义候选识别；失败案例回归；扩展词表 |
| 10 | 敏感词误报 | 普通“healthy lifestyle”被判为医疗功效 | 词表过宽，缺少上下文 | 人审负担增加，用户不信任系统 | FP 统计；reviewer 标记 `over_blocking` | 规则分 severity；低置信语义风险设 warning 而非 blocker |
| 11 | 商品类目判断错误 | 便携榨汁杯被归到普通杯具而非厨房电器 | `category_hint` 模糊；类目映射规则不足 | 加载错误规则包，漏掉电池或食品接触检查 | category confidence 低；risk tags 与类目冲突 | 类目低置信时要求人审；risk tags 独立触发规则 |
| 12 | 规则版本过期 | 使用旧 GPSR demo 规则包 | policy_version 未更新；缓存未失效 | 规则结果不可追溯或不符合当前口径 | run 中 `policy_version` 与 active version 不一致 | 规则版本表；过期版本警告；回归评估绑定版本 |
| 13 | JSON 输出格式错误 | LLM 返回多余解释文本或字段类型错误 | 模型未严格遵守 schema；输出被截断 | 后续校验无法运行 | JSON parser / Pydantic validation fail | JSON repair prompt；重试次数上限；失败后进入人工处理 |
| 14 | Prompt 版本混乱 | 同一 run 不知道用了哪个 prompt | prompt 未版本化或日志缺失 | 无法复现结果 | `GeneratedListing.prompt_version` 为空 | prompt registry；run 创建时固化版本 |
| 15 | 人工审核漏审 | reviewer 未注意 blocker 或误点 approved | UI 信息过载；高风险未强提示 | 风险内容进入导出 | approved 前检查 blocker_count | blocker 未清零禁止导出；审核确认二次提示 |
| 16 | 人工修改未记录 | reviewer 修改了内容但 edit_summary 缺失 | 审核接口未做 diff；直接覆盖原文 | 无法计算人工修改率 | `HumanReview.edit_summary` 为空 | 保存 before/after；自动计算字段级 diff |
| 17 | 导出 payload 字段丢失 | CSV 有标题但缺少 battery_capacity_mah | Adapter 字段映射遗漏 | 下游平台 mock payload 不完整 | export schema validator | 每种 export_profile 配 required_fields；导出前校验 |
| 18 | Run 状态不一致 | `GET /runs` 显示 checked，但 review 已 rejected | 状态机更新非原子；多步骤写入顺序错误 | Demo 解释混乱，难以追踪 | 状态转移校验；审计日志对比 | 用 workflow state transition 表；只允许合法状态迁移 |
| 19 | Trace 丢失 | 某次生成没有 `trace_id` 或 retrieved_chunks | 某节点未传递 context | 无法回放和问责 | trace completeness check | middleware 注入 trace context；缺失 trace 直接 fail fast |
| 20 | 过度自动修复 | 系统自动改掉事实字段，例如材质 | 修复逻辑没有区分事实与表达 | 产生虚假信息 | diff 检查事实字段变化 | facts locked；事实字段只允许人工确认后变更 |

## 2. 必须重点防守的失败链路

### 2.1 RAG 召回错误

最危险的不是没有检索，而是检索到了看似相关但不适用的规则。Mercury 的兜底是：

- `PolicyRule` 必须有 `market_ids`、`category_scope`、`rule_type`、`version`。
- 检索后先做 metadata filter，再交给生成 prompt。
- 合规报告只能引用已存在的 `rule_id`。
- 失败案例标记为 `retrieval_noise` 或 `retrieval_miss`，进入回归集。

### 2.2 LLM 编造规则

LLM 不允许创建新规则。合规解释 prompt 的输出只能使用：

- 输入中的 `PolicyRule.rule_id`。
- validator 返回的 `check_id`。
- `insufficient_evidence`。

如果模型输出未知 `rule_id`，JSON Schema 后的 rule_id reference validator 会拦截。

### 2.3 人工审核漏审

人审不是绝对安全。PoC 中的防线是：

- blocker 未清零时禁止 mock export。
- `reviewer_id`、`reviewed_at`、`decision` 必填。
- 高风险字段修改前后都保留。
- 漏审案例进入失败库，后续优化 UI 或规则提示。

## 3. 失败案例记录模板

```json
{
  "failure_id": "fail_demo_001",
  "run_id": "run_demo_blender_001",
  "trace_id": "trc_demo_blender_001",
  "failure_type": "retrieval_miss",
  "severity": "blocker",
  "description": "DE listing did not retrieve EU responsible person rule.",
  "detected_by": "offline_eval",
  "impact": "ComplianceReport would miss a required field.",
  "root_cause": "Retriever query did not include market region EU.",
  "mitigation": "Add market metadata filter and direct risk-tag rule loading.",
  "regression_sample_id": "eval_blender_de_001",
  "status": "open"
}
```

## 4. 面试回答原则

推荐回答：

> 我不把失败模式藏起来。Mercury 的设计假设 RAG、LLM、规则、人审都可能失败，所以每一层都有检测信号：retrieved_chunks、rule_id、validator_result、human_review_result 和 failure case。PoC 的价值是把失败变成可复现数据，而不是声称模型不会错。
