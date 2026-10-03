from typing import Literal

from app.hybrid_retrieval import hybrid_search
from app.retrieval import search_similar_chunks


RetrievalStrategy = Literal[
    "dense",
    "hybrid"
]


async def retrieve_chunks(
    query: str,
    top_k: int = 5,
    document_id: int | None = None,
    max_distance: float | None = None,
    strategy: RetrievalStrategy = "hybrid"
):
    if strategy == "dense":
        results = await search_similar_chunks(
            query=query,
            top_k=top_k,
            document_id=document_id,
            max_distance=max_distance
        )

        return [
            {
                "chunk": chunk,
                "score": None,
                "distance": float(distance),
                "dense_rank": rank,
                "keyword_rank": None
            }
            for rank, (chunk, distance)
            in enumerate(results, start=1)
        ]

    if strategy == "hybrid":
        return await hybrid_search(
            query=query,
            top_k=top_k,
            document_id=document_id,
            max_distance=max_distance
        )

    raise ValueError(
        f"Unsupported retrieval strategy: {strategy}"
    )