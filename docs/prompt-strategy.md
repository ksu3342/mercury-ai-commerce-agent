# Mercury Prompt Strategy

本文说明 Mercury 的 prompt 和结构化输出策略。核心原则是：prompt 只负责引导模型完成语言和解释任务，关键事实、规则判断和导出边界必须由 schema、validator、rule engine 和人工审核控制。

## 1. 总体原则

| 原则 | 说明 |
|---|---|
| 结构化输出优先 | 所有核心节点输出 JSON，不接受不可解析自由文本 |
| 不编造事实 | 材质、认证、容量、电池、功效必须来自输入或检索片段 |
| 规则只引用 | 模型只能引用已提供的 `rule_id`，不能创造平台政策 |
| 低温生成 | Listing 生成建议 temperature 0.2-0.4，合规解释更低 |
| 失败可修复 | JSON 错误走 repair prompt，规则错误走 validator |
| Prompt 版本化 | 每次 run 记录 `prompt_version` |

## 2. 商品结构化 Prompt

### 解决的问题

用户输入可能是中文标题、规格散文和图片 OCR。结构化 prompt 的目标是把输入整理成 `product_profile`，并暴露缺失字段，不补写事实。

### 输入约束

输入：

- `ProductInput`
- `MarketConfig[]`
- 已知类目列表
- 风险标签规则摘要

禁止：

- 不得新增输入中不存在的事实属性。
- 不得推断认证、测试报告、医疗功效、平台通过结论。
- 不确定字段必须输出 null 或 `missing_attributes`。

### Prompt 模板

```text
You are a product data normalization assistant for a portfolio PoC.

Task:
Normalize the product input into a structured product profile.

Hard rules:
1. Do not invent facts.
2. Only use attributes explicitly present in ProductInput.
3. If a required attribute is missing, add it to missing_attributes.
4. If a risk tag is implied by provided attributes, add it to detected_risk_tags and explain the evidence.
5. Do not claim platform compliance.

Input:
ProductInput:
{{ product_input_json }}

MarketConfig:
{{ market_config_json }}

Allowed categories:
{{ allowed_categories }}

Output JSON schema:
{
  "product_profile": {
    "sku": "string",
    "normalized_category": "string",
    "source_language": "string",
    "target_markets": ["string"],
    "target_languages": ["string"],
    "normalized_attributes": {},
    "detected_risk_tags": ["string"],
    "missing_attributes": [
      {
        "field": "string",
        "required_for": ["string"],
        "severity": "blocker|warning|info",
        "reason": "string"
      }
    ]
  }
}
```

### 输出约束

输出必须符合：

- `normalized_attributes` 只包含输入已有字段。
- `missing_attributes` 必须说明市场和原因。
- 类目置信不足时输出 `normalized_category_confidence < 0.7`，触发人审。

## 3. Listing 生成 Prompt

### 解决的问题

生成多语言 Listing，但不能为了营销效果编造材质、认证、功效或平台政策。

### 输入约束

输入：

- `product_profile`
- `MarketConfig`
- `retrieved_chunks`
- `brand_terms`
- `approved_copy`
- `prompt_version`

禁止：

- 不得写“FDA approved”、“CE certified”等未提供认证。
- 不得扩大材料声明，例如把 Tritan 写成绝对安全。
- 不得生成医疗、减肥、治疗、保证效果。
- 不得翻译 `translation_policy=do_not_translate` 的品牌词。
- 不得删除必填属性，即使值为 null。

### Prompt 模板

```text
You are a multilingual listing generation agent for a controlled portfolio PoC.

Task:
Generate a localized product listing for the target market.

Use only:
- Product facts from product_profile.normalized_attributes.
- Terminology rules from brand_terms.
- Policy context from retrieved_chunks.
- Style hints from approved_copy.

Do not:
1. Invent certifications, test reports, materials, health effects, waterproof ratings, or platform approvals.
2. Create new policy rules.
3. Translate protected brand terms.
4. Remove required fields with null values.
5. Claim that the listing is compliant or approved.

Product profile:
{{ product_profile_json }}

Market config:
{{ market_config_json }}

Retrieved chunks:
{{ retrieved_chunks_json }}

Brand terms:
{{ brand_terms_json }}

Approved copy examples:
{{ approved_copy_json }}

Output JSON schema:
{
  "listing_id": "string",
  "sku": "string",
  "market_id": "string",
  "language": "string",
  "title": "string",
  "bullet_points": ["string"],
  "description": "string",
  "seo_keywords": ["string"],
  "attributes": {},
  "claims": [
    {
      "claim_id": "string",
      "text": "string",
      "claim_type": "usage|material|performance|compliance_sensitive",
      "source_attribute": "string|null"
    }
  ],
  "retrieved_chunks": [
    {
      "chunk_id": "string",
      "rule_id": "string|null",
      "source": "string"
    }
  ],
  "prompt_version": "{{ prompt_version }}",
  "status": "draft"
}
```

### 输出约束

- `title` 长度不直接由 prompt 保证，后续 title validator 检查。
- `claims` 必须列出可能需要规则检查的声明。
- `attributes` 必须保留市场必填字段，缺失时保留 null。

## 4. 合规解释 Prompt

### 解决的问题

规则引擎产生机器结果后，需要生成面向 reviewer 的解释。但解释不能替代规则判断。

### 输入约束

输入：

- `ComplianceReport.checks`
- `PolicyRule[]`
- `GeneratedListing`

禁止：

- 不得新增规则。
- 不得把 warning 说成 blocker。
- 不得给法律结论。
- 不得说 “approved by platform”。

### Prompt 模板

```text
You explain deterministic compliance check results to a human reviewer.

Important:
The checks are already produced by validators and rule engine.
You must not change pass/fail status or severity.
You must not create new rule_id.
You must not provide legal advice.

Input checks:
{{ compliance_checks_json }}

Policy rules:
{{ policy_rules_json }}

Listing:
{{ listing_json }}

Output JSON schema:
{
  "review_summary": "string",
  "blocking_issues": [
    {
      "rule_id": "string",
      "plain_language_reason": "string",
      "suggested_fix": "string"
    }
  ],
  "warnings": [
    {
      "rule_id": "string",
      "plain_language_reason": "string",
      "suggested_fix": "string"
    }
  ],
  "reviewer_notes": ["string"]
}
```

### 输出约束

- `rule_id` 必须来自输入 checks。
- `suggested_fix` 只能基于 remediation 或已知字段。
- 最终审核决定仍由 reviewer 提交。

## 5. JSON Repair Prompt

### 解决的问题

LLM 可能输出非法 JSON。repair prompt 只修格式，不改业务含义。

### 输入约束

输入：

- 原始模型输出。
- JSON parse error。
- 目标 JSON Schema。

禁止：

- 不得新增业务字段。
- 不得补写事实。
- 不得改变原始文本含义。

### Prompt 模板

```text
Repair the following model output into valid JSON.

Rules:
1. Only fix JSON syntax and schema shape.
2. Do not add new facts.
3. Do not remove required fields; use null if value is missing.
4. Do not explain your changes.
5. Return JSON only.

Parse error:
{{ parse_error }}

Target schema:
{{ target_schema_json }}

Invalid output:
{{ invalid_output }}
```

### 输出约束

- repair 后必须再次跑 JSON Schema。
- 最多重试 2 次。
- 仍失败则进入 `json_output_invalid` failure case。

## 6. 如何避免模型编造认证、材质、功效、平台政策

| 风险 | Prompt 约束 | 系统约束 |
|---|---|---|
| 编造认证 | 明确禁止生成未输入认证 | certification validator 检查 `certified`、`approved` 等词 |
| 编造材质 | 只能使用 `normalized_attributes.material` | attributes diff 检查生成属性是否来自输入 |
| 编造功效 | 禁止医疗、治疗、减肥、保证效果 | sensitive term checker + claim classifier |
| 编造平台政策 | 只能引用 `retrieved_chunks.rule_id` | rule_id reference validator |
| 编造平台通过 | 禁止 `approved by platform` | forbidden claim validator |

关键点：prompt 是第一道约束，不是最后一道防线。所有高风险内容都必须由 validator 或 rule engine 检查。

## 7. 为什么关键校验不能只靠 LLM

LLM 输出是概率性的，适合生成语言和总结解释，不适合承担必须稳定的判断。

关键校验包括：

- JSON 字段是否存在。
- 标题长度是否超限。
- 单位和数值是否一致。
- 必填字段是否缺失。
- 禁用词是否出现。
- rule_id 是否存在。
- blocker 是否清零。

这些判断应该由确定性代码完成。LLM 可以帮助解释“为什么失败”和“怎么修”，但不能决定是否放行。

## 8. Prompt 版本管理

每个 prompt 都有版本：

| Prompt | version 示例 | 输出对象 |
|---|---|---|
| 商品结构化 | `product_analyzer_v1.0.0` | `product_profile` |
| Listing 生成 | `listing_generator_v1.0.0` | `GeneratedListing` |
| 合规解释 | `compliance_explainer_v1.0.0` | reviewer summary |
| JSON repair | `json_repair_v1.0.0` | repaired JSON |

每次 run 记录：

- `prompt_version`
- `model_name`
- `retrieved_chunks`
- `validator_result`
- `human_review_result`

Prompt 变更后必须跑同一批 demo/eval 样本，比较：

- JSON 失败率。
- 人工修改率。
- 合规 blocker recall。
- 多语言 rubric 分数。

## 9. 面试防守口径

推荐说法：

> Mercury 的 prompt 不是魔法咒语，而是受 schema 和规则系统约束的任务说明。模型负责把事实组织成多语言内容，确定性系统负责判断格式、字段、单位和规则。这样即使模型出错，也能被检测、修复和回归。
