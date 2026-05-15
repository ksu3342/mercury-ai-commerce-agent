# Mercury RAG Design

本文说明 Mercury 的 RAG 设计。RAG 在本项目中的定位是“提供可追溯上下文”，不是替代规则引擎，也不是让模型自由解释合规。

## 1. RAG 解决什么问题

多语言 Listing 生成需要三类上下文：

1. 平台和市场规则：哪些字段必填、哪些表达高风险。
2. 品牌和术语约束：品牌名、材料名、类目词不能乱翻。
3. 历史优秀文案：给模型提供风格和结构参考。

如果没有 RAG，模型容易凭通用知识生成，看似流畅但不可追溯。RAG 的作用是把生成限制在当前版本规则和可引用样例中。

## 2. 知识来源

| 来源 | 示例 | 用途 | v1 实现 |
|---|---|---|---|
| `policy_chunks` | EU responsible person、battery disclosure、unsupported claims | 合规预检和生成约束 | 本地 JSONL |
| `brand_terms` | Mori 不翻译、Tritan 保留、USB-C 格式 | 术语一致性 | 本地 JSON / CSV |
| `approved_copy` | 已审核通过的标题、卖点、详情 | 风格参考 | 本地 JSONL |
| `market_configs` | 语言、币种、单位、必填字段 | 市场差异约束 | 配置文件 |
| `failure_cases` | 历史误报、漏报、翻译错误 | 回归和 prompt 改进 | JSONL / PostgreSQL |

v1 不抓取实时网页，不把未验证的互联网内容直接入库。所有知识片段必须带 `source_type` 和 `version`。

## 3. 文档切分策略

### 3.1 PolicyRule 切分

规则文档按“一个规则一个 chunk”切分，而不是按固定 token 长度切分。

原因：

- 规则需要稳定 `rule_id`。
- 合规报告要能引用具体规则。
- 固定长度切分可能把 condition、check、remediation 切散。

Policy chunk 示例：

```json
{
  "chunk_id": "policy_eu_gpsr_001",
  "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
  "version": "demo-policy-2026-05",
  "title": "EU responsible person required",
  "content": "EU demo policy requires a responsible person field for selected consumer product categories.",
  "condition_summary": "market.region == EU and category in consumer products",
  "remediation": "Provide responsible_person name, address and contact field."
}
```

### 3.2 Approved Copy 切分

历史优秀文案按 Listing 字段切分：

- title chunk。
- bullet group chunk。
- description chunk。

原因是标题、卖点和详情的写作约束不同。把整篇文案塞给模型会增加噪声。

### 3.3 Brand Terms 切分

术语不按语义 chunk 切分，直接作为 key-value 词典加载：

```json
{
  "term": "Mori",
  "term_type": "brand",
  "translation_policy": "do_not_translate",
  "allowed_forms": ["Mori"]
}
```

## 4. Metadata 设计

每个 chunk 至少包含：

| 字段 | 说明 |
|---|---|
| `chunk_id` | 片段唯一 ID |
| `source_type` | `policy_rule`、`brand_term`、`approved_copy`、`failure_case` |
| `rule_id` | 规则片段必填 |
| `version` | 规则或知识版本 |
| `market_ids` | 适用市场 |
| `languages` | 适用语言 |
| `category_scope` | 适用类目 |
| `risk_tags` | 适用风险标签，例如 `battery` |
| `severity` | `blocker`、`warning`、`info` |
| `effective_from` | 生效时间 |
| `source_url` | v1 可为 `mock://...` |

metadata 的作用是先过滤，再语义召回。这样比“把所有文档丢给 embedding”更可控。

## 5. Embedding 选择

v1 推荐：

- 小规模：Mock retriever 或 FAISS + 多语言 embedding。
- 后续：BGE-M3 或同类多语言 embedding。

选择多语言 embedding 的原因：

- 商品输入可能是中文。
- 输出市场可能是英文和德文。
- 规则片段可能用英文存储。

不直接上重型向量库的原因：

- v1 知识库规模小，性能不是瓶颈。
- 面试重点是检索边界、溯源和评估，不是向量数据库运维。

## 6. 是否需要 Hybrid Retrieval

长期需要，v1 可以先模拟。

原因：

- 规则 ID、字段名、禁用词需要关键词精确匹配。
- 类目、风险描述、历史文案需要语义召回。

推荐检索策略：

```text
candidate_rules = metadata_filter(market, category, risk_tags)
keyword_hits = bm25(rule_id, field_name, forbidden_terms)
semantic_hits = embedding_search(query)
merged = weighted_merge(keyword_hits, semantic_hits)
top_k = rerank_or_score_sort(merged)
```

v1 可以用本地规则直接按 metadata 和关键词返回，文档上保留 hybrid retrieval 设计。

## 7. 是否需要 Rerank

v1 非必须，后续建议加。

不加 rerank 的理由：

- 样本少、规则少，metadata filter 足以保证基本相关性。
- rerank 会增加延迟和实现复杂度。

后续需要 rerank 的触发条件：

- top_k 经常出现不适用规则。
- approved_copy 召回风格不匹配。
- 不同市场规则相似度高，embedding 排序混乱。

rerank 输入必须包含 metadata，不能只看自然语言相似度。

## 8. Rule ID 引用溯源

生成和校验结果必须保留 rule_id。

### 8.1 Listing 中的引用

```json
{
  "retrieved_chunks": [
    {
      "chunk_id": "policy_eu_gpsr_001",
      "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
      "score": 0.94
    }
  ]
}
```

### 8.2 ComplianceReport 中的引用

```json
{
  "check_id": "chk_de_responsible_person",
  "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
  "status": "failed",
  "severity": "blocker"
}
```

### 8.3 约束

- 合规报告不能引用未知 `rule_id`。
- `rule_id` 必须能在当前 `policy_version` 中查到。
- 如果没有足够证据，输出 `insufficient_evidence`，不能编造规则。

## 9. 规则版本管理

规则包按版本管理：

```json
{
  "policy_version": "demo-policy-2026-05",
  "created_at": "2026-05-15T00:00:00Z",
  "status": "active",
  "rules": [
    "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
    "US_UNSUPPORTED_HEALTH_CLAIM",
    "FOOD_CONTACT_MATERIAL_DISCLOSURE"
  ]
}
```

每次 run 固化：

- `policy_version`
- `retriever_version`
- `embedding_model`
- `prompt_version`

规则更新后必须跑回归：

- 历史 blocker 是否仍能识别。
- 历史误报是否减少。
- 新规则是否影响不相关市场。

## 10. 召回失败兜底策略

| 失败 | 检测信号 | 兜底 |
|---|---|---|
| 没有召回任何规则 | `retrieved_chunks.length == 0` | 按 market + risk_tags 加载默认必查规则 |
| 召回不适用市场规则 | chunk `market_ids` 不含目标市场 | 丢弃 chunk，记录 retrieval_noise |
| 缺少 blocker 规则 | gold rule 未出现在 top_k | keyword exact match rule_id / risk tag |
| approved_copy 噪声大 | 风格样例类目不匹配 | 降低 approved_copy 权重，只保留 policy rules |
| 规则版本过期 | chunk version != active policy_version | 标记 warning，禁止生成最终报告 |

## 11. 为什么 RAG 不是用来替代规则引擎

RAG 回答“可以参考什么知识”，规则引擎回答“这个输出是否违反规则”。两者边界不同。

举例：

- RAG 检索到：EU 市场需要 responsible person。
- 规则引擎检查：`attributes.responsible_person` 是否存在。
- ComplianceReport 输出：`rule_id`、status、severity、evidence、suggested_fix。

如果只靠 RAG + LLM 判断，结果会不稳定，也难以回归测试。规则引擎让必须正确的判断可复现。

## 12. MVP 实现边界

MVP 不需要完整 Milvus 集群。推荐最小实现：

- `policy_chunks.jsonl`
- `brand_terms.json`
- `approved_copy.jsonl`
- `MockRetriever.retrieve(query, filters, top_k)`
- metadata filter + keyword match + 固定 score

这样足够演示 RAG 的工程边界。后续替换为 FAISS 或 Milvus 时，`retrieved_chunks` 的接口形状不变。
