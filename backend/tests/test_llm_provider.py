import pytest

from app.generators.mock_listing import MockListingGenerator
from app.llm.json_repair import try_parse_json, validate_generated_listing_payload
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_compatible_provider import OpenAICompatibleProvider
from app.repositories.demo_data import DemoDataRepository
from app.validators.rule_engine import RuleEngine


def test_mock_llm_provider_returns_schema_compatible_listing():
    repo = DemoDataRepository()
    product = repo.get_product_by_sku("MRC-BLEND-450-WH")
    market_config = repo.get_market_config("US")
    provider = MockLLMProvider(repo)

    result = provider.generate_listing_json(
        product=product,
        market_config=market_config,
        retrieved_chunks=repo.get_rag_chunks(),
        prompt_version="listing_generator_v1.1.0",
    )

    assert result.payload["sku"] == "MRC-BLEND-450-WH"
    assert result.payload["market_id"] == "US"
    assert result.model_info["provider"] == "mock_llm"
    assert result.prompt_version == "listing_generator_v1.1.0"
    assert validate_generated_listing_payload(result.payload) == []


def test_listing_generator_uses_llm_provider_boundary():
    repo = DemoDataRepository()
    provider = MockLLMProvider(repo)
    generator = MockListingGenerator(repo, llm_provider=provider)
    product = repo.get_product_by_sku("MRC-BLEND-450-WH")

    listings = generator.generate(
        product=product,
        target_markets=["US"],
        target_languages=["en-US"],
        retrieved_chunks=repo.get_rag_chunks(),
        run_id="run_boundary_test",
        trace_id="trc_boundary_test",
    )

    assert listings[0].run_id == "run_boundary_test"
    assert listings[0].model_info["provider"] == "mock_llm"
    assert listings[0].prompt_version == provider.prompt_version


def test_llm_provider_output_preserves_prompt_version_and_model_info():
    repo = DemoDataRepository()
    provider = MockLLMProvider(repo, prompt_version="listing_generator_v1.1.0")
    product = repo.get_product_by_sku("MRC-CHARGER-65W")
    market_config = repo.get_market_config("DE")

    result = provider.generate_listing_json(
        product=product,
        market_config=market_config,
        retrieved_chunks=repo.get_rag_chunks(),
        prompt_version=provider.prompt_version,
    )

    assert result.prompt_version == "listing_generator_v1.1.0"
    assert result.payload["prompt_version"] == "listing_generator_v1.1.0"
    assert result.payload["model_info"]["provider"] == "mock_llm"
    assert result.payload["model_info"]["model_name"] == "expected-listing-fixture"


def test_json_repair_rejects_invalid_payload_or_reports_error():
    parsed = try_parse_json("{'sku': 'MRC-BLEND-450-WH',}")

    assert parsed.value == {"sku": "MRC-BLEND-450-WH"}
    errors = validate_generated_listing_payload({"sku": "MRC-BLEND-450-WH"})
    assert "missing field: listing_id" in errors
    assert "missing field: title" in errors


def test_real_provider_is_not_called_in_tests():
    provider = OpenAICompatibleProvider(
        base_url="https://llm-gateway.example.invalid/v1",
        api_key="not-used",
        model="not-used",
        enabled=False,
    )

    with pytest.raises(NotImplementedError):
        provider.generate_listing_json(
            product={},
            market_config={},
            retrieved_chunks=[],
            prompt_version="listing_generator_v1.1.0",
        )


def test_generated_listing_still_passes_rule_engine_after_provider_refactor():
    repo = DemoDataRepository()
    product = repo.get_product_by_sku("MRC-BLEND-450-WH")
    generator = MockListingGenerator(repo, llm_provider=MockLLMProvider(repo))
    listings = generator.generate(
        product=product,
        target_markets=["US", "DE"],
        target_languages=["en-US", "de-DE"],
        retrieved_chunks=repo.get_rag_chunks(),
    )

    reports = RuleEngine(
        policy_rules=repo.get_policy_rules(),
        market_configs=repo.get_market_configs(),
    ).check(product=product, listings=listings)

    assert len(reports) == 2
    assert any(report.overall_status == "blocker" for report in reports)
