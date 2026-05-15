from __future__ import annotations

from typing import Iterable, List, Set

from app.repositories import DemoDataRepository
from app.schemas import ProductInput, RagChunk


class MockPolicyRetriever:
    """Deterministic metadata filter over data/demo/policy_chunks.jsonl."""

    def __init__(self, repository: DemoDataRepository) -> None:
        self.repository = repository

    def retrieve(
        self,
        product: ProductInput,
        target_market: str,
        category: str,
        regulatory_tags: Iterable[str],
        top_k: int = 5,
    ) -> List[RagChunk]:
        requested_tags: Set[str] = set(regulatory_tags)
        chunks = self.repository.get_rag_chunks()
        matched: List[RagChunk] = []

        for chunk in chunks:
            if target_market not in chunk.market_ids and "ALL" not in chunk.market_ids:
                continue
            if category not in chunk.category_scope and "all" not in chunk.category_scope:
                continue
            if chunk.risk_tags and not requested_tags.intersection(chunk.risk_tags):
                continue
            matched.append(chunk)

        if product.brand:
            for chunk in chunks:
                if chunk.source_type == "brand_term" and chunk not in matched:
                    matched.append(chunk)

        return sorted(matched, key=lambda item: item.score, reverse=True)[:top_k]
