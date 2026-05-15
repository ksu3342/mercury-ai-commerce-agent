from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from app.repositories import DemoDataRepository
from app.schemas import GeneratedListing, ProductInput, RagChunk, RetrievedChunkRef


PROMPT_VERSION = "listing_generator_v1.0.0"
MODEL_INFO = {
    "provider": "mock_llm",
    "model_name": "qwen3-compatible-demo",
    "temperature": 0.2,
}


class MockListingGenerator:
    """Reads expected demo listings first, then falls back to a fact-only template."""

    def __init__(self, repository: DemoDataRepository) -> None:
        self.repository = repository

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
        expected_by_market = {
            listing.market_id: listing for listing in self.repository.get_expected_listings()
        }
        language_by_market = dict(zip(target_markets, target_languages))
        listings: List[GeneratedListing] = []

        for market_id in target_markets:
            expected = expected_by_market.get(market_id)
            if expected:
                listings.append(
                    expected.model_copy(
                        update={
                            "run_id": run_id,
                            "trace_id": trace_id,
                            "retrieved_chunks": self._enrich_chunk_refs(
                                expected.retrieved_chunks,
                                chunks_by_id,
                            ),
                        },
                        deep=True,
                    )
                )
                continue

            listings.append(
                self._fallback_listing(
                    product=product,
                    market_id=market_id,
                    language=language_by_market.get(market_id, product.target_languages[0]),
                    retrieved_chunks=retrieved_chunks,
                    run_id=run_id,
                    trace_id=trace_id,
                )
            )

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

    def _fallback_listing(
        self,
        product: ProductInput,
        market_id: str,
        language: str,
        retrieved_chunks: List[RagChunk],
        run_id: str,
        trace_id: str,
    ) -> GeneratedListing:
        required_attrs = self.repository.get_market_config(market_id).required_attributes
        attributes = dict(product.attributes)
        missing_fields = [field for field in required_attrs if attributes.get(field) in (None, "")]
        for field in missing_fields:
            attributes.setdefault(field, None)
        if missing_fields:
            attributes["missing_fields"] = missing_fields

        title = f"{product.brand or 'Unknown'} {product.title} {attributes.get('capacity_ml', 'missing')} ml"
        chunk_refs = [
            RetrievedChunkRef(
                chunk_id=chunk.chunk_id,
                rule_id=chunk.rule_id,
                source=chunk.source_type,
                policy_version=chunk.policy_version,
                score=chunk.score,
                text=chunk.text,
            )
            for chunk in retrieved_chunks
            if market_id in chunk.market_ids
        ]

        return GeneratedListing(
            listing_id=f"lst_{product.sku.lower().replace('-', '_')}_{market_id.lower()}",
            run_id=run_id,
            trace_id=trace_id,
            sku=product.sku,
            market_id=market_id,
            language=language,
            title=title,
            bullet_points=[
                "Draft created only from provided product attributes.",
                "Missing required fields are kept as null instead of being invented.",
            ],
            description=product.description or "No source description provided.",
            seo_keywords=[],
            attributes=attributes,
            claims=[],
            retrieved_chunks=chunk_refs,
            prompt_version=PROMPT_VERSION,
            model_info=MODEL_INFO,
            status="draft",
        )
