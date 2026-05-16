from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from app.llm import LLMProvider, MockLLMProvider
from app.llm.json_repair import validate_generated_listing_payload
from app.repositories import DemoDataRepository
from app.schemas import GeneratedListing, ProductInput, RagChunk, RetrievedChunkRef


class MockListingGenerator:
    """Converts LLMProvider JSON output into GeneratedListing models."""

    def __init__(
        self,
        repository: DemoDataRepository,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        self.repository = repository
        self.llm_provider = llm_provider or MockLLMProvider(repository)

    def generate(
        self,
        product: ProductInput,
        target_markets: Iterable[str],
        target_languages: Iterable[str],
        retrieved_chunks: List[RagChunk],
        run_id: str = "run_demo_blender_001",
        trace_id: str = "trc_demo_blender_001",
    ) -> List[GeneratedListing]:
        chunks_by_id = {chunk.chunk_id: chunk for chunk in retrieved_chunks}
        language_by_market = dict(zip(target_markets, target_languages))
        listings: List[GeneratedListing] = []

        for market_id in target_markets:
            market_config = self.repository.get_market_config(market_id)
            provider_result = self.llm_provider.generate_listing_json(
                product=product,
                market_config=market_config,
                retrieved_chunks=retrieved_chunks,
                prompt_version=getattr(self.llm_provider, "prompt_version", "listing_generator_v1.1.0"),
            )
            payload = dict(provider_result.payload)
            validation_errors = validate_generated_listing_payload(payload)
            if validation_errors:
                raise ValueError(f"LLM provider returned invalid listing payload: {validation_errors}")

            refs = [RetrievedChunkRef.model_validate(ref) for ref in payload.get("retrieved_chunks", [])]
            payload.update(
                {
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "language": language_by_market.get(market_id, market_config.language),
                    "prompt_version": provider_result.prompt_version,
                    "model_info": provider_result.model_info,
                    "retrieved_chunks": [
                        ref.model_dump()
                        for ref in self._enrich_chunk_refs(refs, chunks_by_id)
                    ],
                }
            )
            listings.append(GeneratedListing.model_validate(payload))

        return listings

    def _enrich_chunk_refs(
        self,
        refs: List[RetrievedChunkRef],
        chunks_by_id: Dict[str, RagChunk],
    ) -> List[RetrievedChunkRef]:
        enriched: List[RetrievedChunkRef] = []
        for ref in refs:
            chunk: Optional[RagChunk] = chunks_by_id.get(ref.chunk_id)
            if not chunk:
                enriched.append(ref)
                continue
            enriched.append(
                RetrievedChunkRef(
                    chunk_id=chunk.chunk_id,
                    rule_id=chunk.rule_id,
                    source=ref.source or chunk.source_type,
                    policy_version=chunk.policy_version,
                    score=chunk.score,
                    text=chunk.text,
                )
            )
        return enriched
