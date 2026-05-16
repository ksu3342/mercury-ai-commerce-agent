LISTING_GENERATION_SYSTEM_PROMPT = """
You generate marketplace listing JSON for a controlled commerce workflow.
Use only supplied product attributes and retrieved policy chunks.
Do not invent certifications, materials, efficacy, safety proof, platform policy, or legal status.
Mark missing high-risk fields as null or "missing" instead of guessing.
Reference retrieved rule_id values where a claim or required field depends on policy context.
Return JSON only. The output will still be checked by deterministic RuleEngine validators and human review.
""".strip()


LISTING_GENERATION_USER_PROMPT_TEMPLATE = """
Product:
{product_json}

Market config:
{market_config_json}

Retrieved policy chunks:
{retrieved_chunks_json}

Create one draft listing JSON for the requested market. High-risk claims, missing compliance fields,
and broad compatibility or safety language must remain reviewable by a human reviewer.
""".strip()


COMPLIANCE_EXPLANATION_PROMPT_TEMPLATE = """
Explain compliance issues using only the supplied rule_id, evidence, and suggested_fix fields.
Do not add new policy claims or legal conclusions.
""".strip()
