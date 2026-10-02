from app.keyword_retrieval import (
    search_keyword_chunks
)
from app.retrieval import (
    search_similar_chunks
)


async def hybrid_search(
    query: str,
    top_k: int = 5,
    document_id: int | None = None,
    max_distance: float | None = None,
    rrf_k: int = 60
):
    dense_results = await search_similar_chunks(
        query=query,
        top_k=top_k,
        max_distance=max_distance,
        document_id=document_id
    )

    keyword_results = search_keyword_chunks(
        query=query,
        top_k=top_k,
        document_id=document_id
    )

    combined = {}

    for rank, (
        chunk,
        distance
    ) in enumerate(
        dense_results,
        start=1
    ):
        chunk_id = chunk.id

        if chunk_id not in combined:
            combined[chunk_id] = {
                "chunk": chunk,
                "score": 0.0,
                "dense_rank": None,
                "keyword_rank": None,
                "distance": float(
                    distance
                )
            }

        combined[chunk_id][
            "score"
        ] += 1 / (
            rrf_k + rank
        )

        combined[chunk_id][
            "dense_rank"
        ] = rank

    for rank, (
        chunk,
        keyword_score
    ) in enumerate(
        keyword_results,
        start=1
    ):
        chunk_id = chunk.id

        if chunk_id not in combined:
            combined[chunk_id] = {
                "chunk": chunk,
                "score": 0.0,
                "dense_rank": None,
                "keyword_rank": None,
                "distance": None
            }

        combined[chunk_id][
            "score"
        ] += 1 / (
            rrf_k + rank
        )

        combined[chunk_id][
            "keyword_rank"
        ] = rank

    results = sorted(
        combined.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]