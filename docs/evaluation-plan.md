# Mercury 评估方案

Mercury 的评估目标不是证明模型“文案写得漂亮”，而是证明系统能稳定地产出可审核、可修复、可追溯的多语言 Listing 草稿。

第一性原理：LLM 应用的质量来自三部分。第一是输入是否被正确结构化；第二是生成是否满足业务和语言要求；第三是系统是否能发现错误并把错误转成可行动的修复建议。

## 1. 离线评测集怎么构造

### 1.1 样本规模

PoC 阶段建议准备 100-200 条样本，足够面试演示和指标计算。

建议分布：

| 类别 | 数量 | 目的 |
|---|---:|---|
| 正常商品样本 | 50 | 验证常规生成质量和属性完整率 |
| 属性缺失样本 | 30 | 验证缺失字段识别能力 |
| 高风险规则样本 | 30 | 验证合规识别 recall |
| 多语言挑战样本 | 30 | 验证术语、本地化、单位和语气 |
| 失败回归样本 | 20 | 验证系统是否修复历史问题 |

### 1.2 类目选择

v1 不追求覆盖全平台，建议选择 2-3 个容易解释且有规则压力的类目：

- 厨房用品：涉及食品接触材料、容量、材质。
- 消费电子配件：涉及电池、充电、规格参数。
- 美妆个护：涉及功效声明、敏感词、夸大宣传。

### 1.3 每条样本包含什么

每条评测样本建议包含：

```json
{
  "sample_id": "eval_001",
  "product_input": {
    "sku": "SKU-EVAL-001",
    "title": "便携榨汁杯",
    "category_hint": "kitchen_appliance",
    "target_markets": ["US", "DE"],
    "target_languages": ["en-US", "de-DE"],
    "attributes": {
      "capacity_ml": 450,
      "material": "Tritan",
      "battery_capacity_mah": 5000
    },
    "regulatory_tags": ["battery", "food_contact"]
  },
  "gold_required_attributes": [
    "capacity_ml",
    "material",
    "battery_capacity_mah",
    "responsible_person"
  ],
  "gold_policy_issues": [
    {
      "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
      "severity": "blocker",
      "expected_status": "failed"
    }
  ],
  "gold_language_notes": {
    "en-US": ["avoid unsupported health claims", "use US spelling"],
    "de-DE": ["use metric units", "avoid unverifiable safety guarantee"]
  }
}
```

## 2. 属性完整率

### 解决的问题

Listing 发布失败很大一部分来自必填属性缺失。属性完整率衡量系统是否能把商品资料补齐到可审核状态。

### 指标定义

```text
属性完整率 = 已填写且格式正确的必填属性数 / gold_required_attributes 总数
```

按市场和类目分别统计：

```text
attribute_completeness(market, category)
```

### 验收标准

PoC 目标：

- 整体属性完整率 >= 95%。
- 高风险类目属性完整率 >= 90%。
- 如果属性不能确定，系统必须输出 `missing_attributes` 或 `needs_human_input`，不能让模型编造。

### 面试解释

这个指标证明系统不是只会生成自然语言，而是知道平台发布依赖结构化字段。对于不确定字段，我宁愿让系统暴露缺失，也不让模型猜。

## 3. 合规识别 Precision / Recall

### 解决的问题

合规检查的核心不是“看起来严格”，而是能发现该发现的问题，同时不过度误报导致人工无法使用。

### 标签定义

每个规则检查有四种结果：

| 结果 | 含义 |
|---|---|
| TP | 样本确实有问题，系统识别出来 |
| FP | 样本没有问题，系统误报 |
| FN | 样本有问题，系统漏报 |
| TN | 样本没有问题，系统正确放行 |

### 指标公式

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
```

建议按 severity 拆分：

- `blocker_recall`
- `blocker_precision`
- `warning_recall`
- `warning_precision`

### 验收标准

PoC 目标：

- blocker recall >= 85%。
- blocker precision >= 80%。
- warning precision 可以略低，但要在报告中说明。

### 面试解释

合规系统优先保证高风险问题不漏报，所以 blocker recall 比 warning precision 更重要。但如果误报太高，人审会失去信任，所以 precision 也必须跟踪。

## 4. 人工修改率

### 解决的问题

生成质量最终要看审核者需要改多少。人工修改率比“模型自评 9 分”更接近 PoC 的可用性判断。

### 指标定义

可用字符级或字段级估算。PoC 推荐字段级，解释更简单：

```text
人工修改率 = 被人工修改的字段数 / 可编辑字段总数
```

字段包括：

- `title`
- `bullet_points`
- `description`
- `seo_keywords`
- `attributes`
- `claims`

也可以记录更细的估算：

```text
estimated_edit_rate = edit_distance(original_text, reviewed_text) / len(original_text)
```

### 验收标准

PoC 目标：

- 平均人工修改率 <= 25%。
- `approved` 样本占比 >= 70%。
- `rejected` 样本必须进入失败案例库。

### 面试解释

这个指标能证明系统在业务上减少了人工工作，而不是只生成一段需要重写的文本。比单纯 BLEU 或 ROUGE 更适合内容生产场景。

## 5. 多语言质量评估

### 解决的问题

多语言 Listing 不只是翻译正确，还要市场适配、术语一致和风险声明克制。

### 评估维度

建议采用人工 rubric + 自动检查结合。

| 维度 | 评分 | 说明 |
|---|---:|---|
| Meaning Preservation | 1-5 | 是否保留原始商品事实 |
| Terminology Consistency | 1-5 | 品牌术语和类目术语是否一致 |
| Locale Fit | 1-5 | 是否符合目标市场表达习惯 |
| Compliance Tone | 1-5 | 是否避免夸大、绝对化、医疗化表述 |
| Readability | 1-5 | 是否通顺、清晰、适合 Listing |

### 自动检查

自动检查不替代人工评分，只作为辅助：

- 语言代码是否匹配目标语言。
- 单位是否符合市场配置。
- 禁用词是否出现。
- 品牌词是否被错误翻译。
- 标题长度是否超限。
- 数值是否与输入属性一致。

### 验收标准

PoC 目标：

- 人工平均分 >= 4/5。
- 品牌术语错误率 <= 5%。
- 关键数值一致性错误率 = 0。

### 面试解释

多语言质量不适合只用通用翻译指标，因为 Listing 是受平台规则约束的商业内容。我会用人工 rubric 评估语言质量，用确定性检查保证数值、单位、术语这些不能错的部分。

## 6. 失败案例库

### 解决的问题

LLM 系统一定会失败。关键不是假装不失败，而是把失败变成可复现、可修复、可回归的资产。

### 失败案例结构

```json
{
  "failure_id": "fail_20260515_001",
  "run_id": "run_20260515_0001",
  "trace_id": "trc_9fd2a1",
  "sku": "SKU-1001",
  "market_id": "DE",
  "failure_type": "missing_required_field",
  "severity": "blocker",
  "input_snapshot": {
    "title": "便携榨汁杯",
    "regulatory_tags": ["battery", "food_contact"]
  },
  "model_output_snapshot": {
    "listing_id": "lst_1001_de",
    "title": "Tragbarer Mixer 450 ml mit USB-C-Ladung"
  },
  "validator_result": {
    "failed_rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED"
  },
  "human_review_result": {
    "decision": "changes_requested",
    "failure_tags": ["missing_required_field", "claim_too_strong"]
  },
  "root_cause": "MarketConfig required responsible_person but generator did not preserve the null field in final payload.",
  "fix_plan": "Add rule-aware required field preservation and regression test.",
  "status": "open"
}
```

### 分类方式

| 失败类型 | 例子 |
|---|---|
| `missing_required_field` | EU 市场缺少 responsible_person |
| `unsupported_claim` | 生成“100% safe”或医疗功效 |
| `attribute_hallucination` | 输入没有防水等级，模型生成 IPX7 |
| `unit_error` | ml 被错误换成 oz 或数值不一致 |
| `terminology_error` | 品牌词被翻译 |
| `retrieval_miss` | 未检索到相关规则 |
| `over_blocking` | 普通卖点被误判为合规 blocker |

### 面试解释

失败案例库证明我知道 LLM 应用不是一次 prompt 调好就结束。真正的工程闭环是：失败记录、根因分析、规则或 prompt 修复、回归评估。

## 7. 可观测指标

每次 run 记录：

| 指标 | 目的 |
|---|---|
| `trace_id` | 链路回放 |
| `prompt_version` | prompt 变更对比 |
| `policy_version` | 规则版本回溯 |
| `retrieved_chunks` | 检索依据审计 |
| `validator_result` | 机器校验结果 |
| `human_review_result` | 人审质量反馈 |
| `latency_ms` | 性能瓶颈分析 |
| `token_usage` | 成本估算 |
| `status_transition` | 状态机异常定位 |

PoC 可先写入 PostgreSQL 或 JSONL 文件。生产化再接 OpenTelemetry、Prometheus、LangSmith 等工具。

## 8. 面试时如何解释这些指标

### 8.1 推荐总述

我不会只说“模型生成得不错”，因为这不可验证。我把 Mercury 的质量拆成四层：输入结构化是否完整、合规风险是否识别、生成内容是否减少人工编辑、失败是否能回归修复。

### 8.2 指标解释话术

| 指标 | 面试解释 |
|---|---|
| 属性完整率 | 证明系统理解发布依赖结构化字段，而不是只生成自然语言 |
| 合规 recall | 证明高风险问题尽量不漏报 |
| 合规 precision | 防止误报太多导致人审不信任系统 |
| 人工修改率 | 衡量系统是否真的减少运营工作量 |
| 多语言 rubric | 衡量语言、本地化、术语和合规语气 |
| 失败案例库 | 证明系统能从错误中迭代，而不是一次性 Demo |
| trace 覆盖率 | 证明每次生成可以回放和追责 |

### 8.3 不夸大的边界

可以说：

> Mercury 在演示样本中把“草稿准备 + 初步合规检查”拆成可追踪流程，并用人工修改率、合规检查结果和失败案例衡量是否减少重复编辑。

不要说：

> Mercury 可以替代平台审核或法律合规判断。

更稳健的说法：

> 它做的是合规预检和风险分级，不替代法务或平台最终审核。它的价值是把明显错误提前暴露，把人工审核从全量重写变成重点确认。

## 9. 最小验收清单

文档和 Demo 达到以下标准即可用于面试：

- 至少 100 条离线样本。
- 至少 20 条带 gold policy issue 的高风险样本。
- 每次 run 都能查到 `trace_id`、`prompt_version`、`retrieved_chunks`、`validator_result`、`human_review_result`。
- 能展示 1 个通过样本、1 个 warning 样本、1 个 blocker 样本。
- 能展示一次人工审核如何降低风险并形成失败案例。
- 能用指标解释“为什么它不是普通文案生成工具”。
