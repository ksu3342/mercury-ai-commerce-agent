# Mercury Demo Case: Portable Blender / 便携榨汁杯

本文设计一个 5-8 分钟可讲清的完整演示案例。案例目标不是证明 Mercury 已经接入真实平台，而是展示一个 PoC 如何把商品资料转成多语言 Listing 草稿、合规报告、人工审核记录和 Mock 导出 payload。

## 1. 讲解节奏

| 时间 | 内容 | 面试重点 |
|---:|---|---|
| 0:00-1:00 | 展示原始 ProductInput | 输入不完整、包含电池和食品接触风险 |
| 1:00-2:00 | 展示 Agent 执行步骤 | 状态机不是自由聊天 |
| 2:00-3:30 | 展示 RAG 检索和生成结果 | 英文、德文 Listing 都有规则来源 |
| 3:30-5:00 | 展示合规报告 | EU responsible_person blocker，敏感声明 warning |
| 5:00-6:30 | 展示人工审核 | 人审修改被记录为评估数据 |
| 6:30-8:00 | 展示导出和 run trace | Mock payload + trace_id + validator_result |

## 2. 原始输入 ProductInput JSON

```json
{
  "product_id": "prod_demo_blender_001",
  "sku": "MRC-BLEND-450-WH",
  "source_language": "zh-CN",
  "title": "便携榨汁杯",
  "description": "450ml 便携榨汁杯，Tritan 杯体，USB-C 充电，适合办公室、健身和户外使用。",
  "brand": "Mori",
  "category_hint": "kitchen_appliance",
  "target_markets": ["US", "DE"],
  "target_languages": ["en-US", "de-DE"],
  "attributes": {
    "capacity_ml": 450,
    "material": "Tritan",
    "battery_capacity_mah": 5000,
    "charger_type": "USB-C",
    "color": "white",
    "weight_g": 620,
    "blade_material": "stainless_steel"
  },
  "image_assets": [
    {
      "url": "mock://images/mrc-blend-450-main.jpg",
      "alt_text": "white portable blender cup with USB-C charging base",
      "ocr_text": "450ml USB-C Portable Blender"
    }
  ],
  "regulatory_tags": ["battery", "food_contact"],
  "source_metadata": {
    "source": "manual_upload",
    "uploaded_by": "demo_operator",
    "batch_id": "demo_batch_20260515"
  }
}
```

## 3. 目标市场和语言

| 市场 | 语言 | 规则重点 | 单位 |
|---|---|---|---|
| US | en-US | 避免 unsupported health claims；保留电池容量字段 | metric + optional imperial |
| DE | de-DE | EU responsible_person；食品接触材料声明谨慎；电池字段 | metric |

## 4. Agent 执行步骤

| 步骤 | 状态节点 | 调用工具 | 输入 | 输出 |
|---:|---|---|---|---|
| 1 | `AnalyzeProduct` | `ProductAnalyzer`、JSON Schema validator | ProductInput | `product_profile`、风险标签、缺失字段 |
| 2 | `RetrieveContext` | `PolicyRetriever`、`TerminologyRetriever`、`ApprovedCopyRetriever` | sku、market、category、risk tags | `retrieved_chunks` |
| 3 | `GenerateListing` | `LLMProvider.generate_json` | product_profile、market_config、retrieved_chunks | en-US / de-DE `GeneratedListing` |
| 4 | `ValidateListing` | JSON Schema validator、rule engine、unit validator、sensitive term checker、image-text checker | GeneratedListing | `ComplianceReport` |
| 5 | `PrepareReview` | `ReviewTaskBuilder` | listings、reports | 人审任务 |
| 6 | `SubmitReview` | `HumanReviewRecorder` | 人工修改和决定 | `HumanReview` |
| 7 | `ExportPayload` | `CsvExportAdapter`、`JsonExportAdapter`、`ShopifyLikeAdapter` | approved listing | CSV / JSON payload |
| 8 | `GetRun` | `RunRepository` | run_id | run 状态和 trace 汇总 |

## 5. 检索到的规则和片段

```json
[
  {
    "chunk_id": "policy_us_claims_001",
    "rule_id": "US_UNSUPPORTED_HEALTH_CLAIM",
    "policy_version": "demo-policy-2026-05",
    "market_id": "US",
    "source": "mock_policy_pack",
    "score": 0.89,
    "text": "Do not claim that a consumer product cures, treats, or guarantees health outcomes unless supported by approved evidence."
  },
  {
    "chunk_id": "policy_eu_gpsr_001",
    "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
    "policy_version": "demo-policy-2026-05",
    "market_id": "DE",
    "source": "mock_policy_pack",
    "score": 0.94,
    "text": "EU demo policy requires a responsible person field for selected consumer product categories."
  },
  {
    "chunk_id": "policy_food_contact_001",
    "rule_id": "FOOD_CONTACT_MATERIAL_DISCLOSURE",
    "policy_version": "demo-policy-2026-05",
    "market_id": "DE",
    "source": "mock_policy_pack",
    "score": 0.86,
    "text": "Food contact material statements must be based on provided material attributes and should avoid broad safety guarantees."
  },
  {
    "chunk_id": "policy_battery_001",
    "rule_id": "BATTERY_CAPACITY_FIELD_REQUIRED",
    "policy_version": "demo-policy-2026-05",
    "market_id": "US",
    "source": "mock_policy_pack",
    "score": 0.82,
    "text": "Products containing rechargeable batteries should preserve battery capacity and charging type in structured attributes."
  },
  {
    "chunk_id": "term_brand_001",
    "rule_id": "BRAND_TERM_DO_NOT_TRANSLATE",
    "policy_version": "brand-terms-2026-05",
    "market_id": "ALL",
    "source": "brand_terms",
    "score": 0.97,
    "text": "Brand name Mori must not be translated or localized."
  }
]
```

## 6. 生成的英文 Listing

```json
{
  "listing_id": "lst_demo_blender_us",
  "run_id": "run_demo_blender_001",
  "trace_id": "trc_demo_blender_001",
  "sku": "MRC-BLEND-450-WH",
  "market_id": "US",
  "language": "en-US",
  "title": "Mori Portable 450 ml USB-C Blender Cup",
  "bullet_points": [
    "450 ml cup for smoothies, juice and protein drinks",
    "USB-C charging with 5000 mAh battery capacity based on provided SKU data",
    "Tritan cup and stainless steel blades for everyday drink preparation",
    "Compact white design for office, gym and travel routines"
  ],
  "description": "The Mori portable blender cup is designed for quick everyday drinks at work, at the gym or on short trips. The 450 ml cup, USB-C charging and compact body make it suitable for simple drink preparation. Review battery, material and local compliance fields before publishing.",
  "seo_keywords": ["portable blender", "usb c blender", "smoothie cup", "travel blender"],
  "attributes": {
    "capacity_ml": 450,
    "material": "Tritan",
    "battery_capacity_mah": 5000,
    "charger_type": "USB-C",
    "color": "white",
    "blade_material": "stainless_steel"
  },
  "claims": [
    {
      "claim_id": "clm_us_001",
      "text": "for smoothies, juice and protein drinks",
      "claim_type": "usage"
    }
  ],
  "retrieved_chunks": [
    {"chunk_id": "policy_us_claims_001", "rule_id": "US_UNSUPPORTED_HEALTH_CLAIM"},
    {"chunk_id": "policy_battery_001", "rule_id": "BATTERY_CAPACITY_FIELD_REQUIRED"},
    {"chunk_id": "term_brand_001", "rule_id": "BRAND_TERM_DO_NOT_TRANSLATE"}
  ],
  "prompt_version": "listing_generator_v1.0.0",
  "model_info": {
    "provider": "mock_llm",
    "model_name": "qwen3-compatible-demo",
    "temperature": 0.2
  },
  "status": "draft"
}
```

## 7. 生成的德文 Listing

```json
{
  "listing_id": "lst_demo_blender_de",
  "run_id": "run_demo_blender_001",
  "trace_id": "trc_demo_blender_001",
  "sku": "MRC-BLEND-450-WH",
  "market_id": "DE",
  "language": "de-DE",
  "title": "Mori tragbarer Mixer 450 ml mit USB-C-Ladung",
  "bullet_points": [
    "450 ml Becher fuer Smoothies, Saefte und einfache Mixgetraenke",
    "USB-C-Ladung und 5000 mAh Akkukapazitaet gemaess bereitgestellten SKU-Daten",
    "Tritan-Becher und Edelstahlklingen fuer die taegliche Zubereitung",
    "Kompaktes weisses Design fuer Buero, Fitnessstudio und kurze Reisen"
  ],
  "description": "Der tragbare Mori Mixer ist fuer schnelle Getraenke im Alltag konzipiert. Die Angaben zu Material, Akku und Kapazitaet basieren auf den bereitgestellten Produktdaten. Vor der Veroeffentlichung muessen EU-spezifische Pflichtfelder und lokale Compliance-Hinweise geprueft werden.",
  "seo_keywords": ["tragbarer mixer", "usb c mixer", "smoothie becher", "mixer fuer unterwegs"],
  "attributes": {
    "capacity_ml": 450,
    "material": "Tritan",
    "battery_capacity_mah": 5000,
    "charger_type": "USB-C",
    "color": "white",
    "blade_material": "stainless_steel",
    "responsible_person": null
  },
  "claims": [
    {
      "claim_id": "clm_de_001",
      "text": "fuer die taegliche Zubereitung",
      "claim_type": "usage"
    }
  ],
  "retrieved_chunks": [
    {"chunk_id": "policy_eu_gpsr_001", "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED"},
    {"chunk_id": "policy_food_contact_001", "rule_id": "FOOD_CONTACT_MATERIAL_DISCLOSURE"},
    {"chunk_id": "term_brand_001", "rule_id": "BRAND_TERM_DO_NOT_TRANSLATE"}
  ],
  "prompt_version": "listing_generator_v1.0.0",
  "model_info": {
    "provider": "mock_llm",
    "model_name": "qwen3-compatible-demo",
    "temperature": 0.2
  },
  "status": "draft"
}
```

## 8. 合规检查报告

```json
{
  "report_id": "rpt_demo_blender_001",
  "run_id": "run_demo_blender_001",
  "trace_id": "trc_demo_blender_001",
  "policy_version": "demo-policy-2026-05",
  "overall_status": "blocker",
  "reports": [
    {
      "report_id": "rpt_demo_blender_us",
      "listing_id": "lst_demo_blender_us",
      "market_id": "US",
      "overall_status": "warning",
      "score": 88,
      "policy_version": "demo-policy-2026-05",
      "retrieved_chunks": [
        {
          "chunk_id": "policy_battery_001",
          "rule_id": "BATTERY_CAPACITY_FIELD_REQUIRED",
          "source": "mock_policy_pack",
          "score": 0.82
        },
        {
          "chunk_id": "policy_us_claims_001",
          "rule_id": "US_UNSUPPORTED_HEALTH_CLAIM",
          "source": "mock_policy_pack",
          "score": 0.89
        }
      ],
      "checks": [
        {
          "check_id": "chk_us_battery_capacity",
          "rule_id": "BATTERY_CAPACITY_FIELD_REQUIRED",
          "status": "passed",
          "severity": "warning",
          "message": "电池容量和充电类型已保留在结构化属性中。",
          "evidence": {
            "battery_capacity_mah": 5000,
            "charger_type": "USB-C"
          },
          "suggested_fix": null
        },
        {
          "check_id": "chk_us_health_claim",
          "rule_id": "US_UNSUPPORTED_HEALTH_CLAIM",
          "status": "passed",
          "severity": "blocker",
          "message": "未发现治疗、减肥或保证健康结果的高风险声明。",
          "evidence": {
            "matched_terms": []
          },
          "suggested_fix": null
        }
      ],
      "validator_result": {
        "json_schema_passed": true,
        "failed_validator_count": 0,
        "warning_count": 1,
        "blocker_count": 0
      }
    },
    {
      "report_id": "rpt_demo_blender_de",
      "listing_id": "lst_demo_blender_de",
      "market_id": "DE",
      "overall_status": "blocker",
      "score": 74,
      "policy_version": "demo-policy-2026-05",
      "retrieved_chunks": [
        {
          "chunk_id": "policy_eu_gpsr_001",
          "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
          "source": "mock_policy_pack",
          "score": 0.94
        },
        {
          "chunk_id": "policy_food_contact_001",
          "rule_id": "FOOD_CONTACT_MATERIAL_DISCLOSURE",
          "source": "mock_policy_pack",
          "score": 0.86
        }
      ],
      "checks": [
        {
          "check_id": "chk_de_responsible_person",
          "rule_id": "EU_GPSR_RESPONSIBLE_PERSON_REQUIRED",
          "status": "failed",
          "severity": "blocker",
          "message": "DE/EU 市场缺少 responsible_person 字段。",
          "evidence": {
            "field": "attributes.responsible_person",
            "value": null
          },
          "suggested_fix": "补充 EU 负责人信息；Demo 中可使用 Mock 企业信息。"
        },
        {
          "check_id": "chk_de_food_contact_tone",
          "rule_id": "FOOD_CONTACT_MATERIAL_DISCLOSURE",
          "status": "warning",
          "severity": "warning",
          "message": "食品接触相关表达应保持克制，避免绝对安全承诺。",
          "evidence": {
            "claim": "Tritan-Becher und Edelstahlklingen fuer die taegliche Zubereitung"
          },
          "suggested_fix": "保留材质事实，不写 100% safe 或 medically safe。"
        }
      ],
      "validator_result": {
        "json_schema_passed": true,
        "failed_validator_count": 1,
        "warning_count": 1,
        "blocker_count": 1
      }
    }
  ]
}
```

## 9. 人工审核修改记录

```json
{
  "review_id": "rev_demo_blender_de",
  "run_id": "run_demo_blender_001",
  "trace_id": "trc_demo_blender_001",
  "listing_id": "lst_demo_blender_de",
  "reviewer_id": "reviewer_demo_01",
  "decision": "changes_requested",
  "comments": "补充 EU responsible_person，并保留材质事实，不扩大食品接触安全含义。",
  "edited_listing": {
    "title": "Mori tragbarer Mixer 450 ml mit USB-C-Ladung",
    "bullet_points": [
      "450 ml Becher fuer Smoothies, Saefte und einfache Mixgetraenke",
      "USB-C-Ladung und 5000 mAh Akkukapazitaet gemaess bereitgestellten SKU-Daten",
      "Tritan-Becher und Edelstahlklingen; Materialangaben vor Veroeffentlichung pruefen",
      "Kompaktes weisses Design fuer Buero, Fitnessstudio und kurze Reisen"
    ],
    "attributes": {
      "responsible_person": {
        "name": "Demo EU Responsible Person GmbH",
        "address": "Mockstrasse 1, 10115 Berlin, Germany",
        "email": "compliance@example.invalid"
      }
    }
  },
  "edit_summary": {
    "title_changed": false,
    "bullet_points_changed": true,
    "description_changed": false,
    "attributes_changed": true,
    "estimated_edit_rate": 0.16
  },
  "human_review_result": {
    "quality_score": 4,
    "compliance_confidence": "medium",
    "needs_regeneration": false,
    "failure_tags": ["missing_required_field", "claim_too_broad"]
  },
  "reviewed_at": "2026-05-15T10:15:00Z"
}
```

## 10. 最终导出的 CSV

```csv
sku,market_id,language,title,bullet_1,bullet_2,bullet_3,bullet_4,capacity_ml,material,battery_capacity_mah,charger_type,responsible_person_name,status
MRC-BLEND-450-WH,US,en-US,"Mori Portable 450 ml USB-C Blender Cup","450 ml cup for smoothies, juice and protein drinks","USB-C charging with 5000 mAh battery capacity based on provided SKU data","Tritan cup and stainless steel blades for everyday drink preparation","Compact white design for office, gym and travel routines",450,Tritan,5000,USB-C,,approved_for_mock_export
MRC-BLEND-450-WH,DE,de-DE,"Mori tragbarer Mixer 450 ml mit USB-C-Ladung","450 ml Becher fuer Smoothies, Saefte und einfache Mixgetraenke","USB-C-Ladung und 5000 mAh Akkukapazitaet gemaess bereitgestellten SKU-Daten","Tritan-Becher und Edelstahlklingen; Materialangaben vor Veroeffentlichung pruefen","Kompaktes weisses Design fuer Buero, Fitnessstudio und kurze Reisen",450,Tritan,5000,USB-C,"Demo EU Responsible Person GmbH",approved_for_mock_export
```

## 11. 最终导出的 JSON / Shopify-like payload

```json
{
  "export_id": "exp_demo_blender_001",
  "run_id": "run_demo_blender_001",
  "trace_id": "trc_demo_blender_001",
  "export_type": "shopify_like_json",
  "is_real_platform_request": false,
  "items": [
    {
      "sku": "MRC-BLEND-450-WH",
      "market_id": "US",
      "language": "en-US",
      "handle": "mori-portable-blender-450ml-us",
      "title": "Mori Portable 450 ml USB-C Blender Cup",
      "vendor": "Mori",
      "body_html": "<p>The Mori portable blender cup is designed for quick everyday drinks at work, at the gym or on short trips.</p>",
      "tags": ["portable_blender", "usb_c", "battery", "mock_export"],
      "metafields": {
        "capacity_ml": 450,
        "material": "Tritan",
        "battery_capacity_mah": 5000,
        "charger_type": "USB-C"
      }
    },
    {
      "sku": "MRC-BLEND-450-WH",
      "market_id": "DE",
      "language": "de-DE",
      "handle": "mori-tragbarer-mixer-450ml-de",
      "title": "Mori tragbarer Mixer 450 ml mit USB-C-Ladung",
      "vendor": "Mori",
      "body_html": "<p>Der tragbare Mori Mixer ist fuer schnelle Getraenke im Alltag konzipiert.</p>",
      "tags": ["tragbarer_mixer", "usb_c", "battery", "mock_export"],
      "metafields": {
        "capacity_ml": 450,
        "material": "Tritan",
        "battery_capacity_mah": 5000,
        "charger_type": "USB-C",
        "responsible_person": {
          "name": "Demo EU Responsible Person GmbH",
          "address": "Mockstrasse 1, 10115 Berlin, Germany",
          "email": "compliance@example.invalid"
        }
      }
    }
  ],
  "observability": {
    "prompt_version": "listing_generator_v1.0.0",
    "policy_version": "demo-policy-2026-05",
    "validator_result": {
      "json_schema_passed": true,
      "failed_validator_count_after_review": 0,
      "warning_count_after_review": 1,
      "blocker_count_after_review": 0
    },
    "human_review_result": {
      "estimated_edit_rate": 0.16,
      "decision": "changes_requested_then_exported"
    }
  }
}
```

## 12. 面试讲解总结

推荐收束语：

> 这个 Demo 展示的不是模型会写两种语言，而是受控 Agent 如何把商品资料变成可审核内容。RAG 提供规则和术语依据，结构化输出让结果可校验，规则引擎发现 EU blocker，人审补齐责任字段，最后只导出 Mock payload。这个闭环能说明我理解 LLM 应用的风险边界，而不是把模型输出直接发布。
