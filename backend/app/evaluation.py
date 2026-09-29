from app.retrieval import search_similar_chunks


async def evaluate_retrieval_case(
    query: str,
    expected_document_id: int,
    expected_page: int | None = None,
    top_k: int = 3,
    max_distance: float | None = None
):
    results = await search_similar_chunks(
        query=query,
        top_k=top_k,
        max_distance=max_distance
    )

    retrieved = []

    first_relevant_rank = None

    for rank, (chunk, distance) in enumerate(
        results,
        start=1
    ):
        is_relevant = (
            chunk.document_id == expected_document_id
        )

        if expected_page is not None:
            is_relevant = (
                is_relevant
                and chunk.page_number == expected_page
            )

        if is_relevant and first_relevant_rank is None:
            first_relevant_rank = rank

        retrieved.append({
            "rank": rank,
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document": chunk.document.filename,
            "page": chunk.page_number,
            "distance": float(distance),
            "relevant": is_relevant
        })

    hit = first_relevant_rank is not None

    reciprocal_rank = (
        1 / first_relevant_rank
        if first_relevant_rank
        else 0
    )

    return {
        "query": query,
        "hit": hit,
        "first_relevant_rank": first_relevant_rank,
        "reciprocal_rank": reciprocal_rank,
        "retrieved": retrieved
    }