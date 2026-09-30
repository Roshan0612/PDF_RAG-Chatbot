from app.tokenization import count_tokens


def build_context(
    results,
    max_tokens: int = 2000
):
    context_parts = []
    sources = []

    used_tokens = 0

    for index, (chunk, distance) in enumerate(
        results,
        start=1
    ):
        source_id = f"S{index}"

        part = (
            f"[{source_id}]\n"
            f"Document: {chunk.document.filename}\n"
            f"Page: {chunk.page_number}\n"
            f"{chunk.content}"
        )

        part_tokens = count_tokens(
            part
        )

        if used_tokens + part_tokens > max_tokens:
            break

        context_parts.append(
            part
        )

        sources.append({
            "source_id": source_id,
            "chunk_id": chunk.id,
            "document": chunk.document.filename,
            "page": chunk.page_number,
            "distance": float(distance)
        })

        used_tokens += part_tokens

    return {
        "context": "\n\n".join(
            context_parts
        ),
        "sources": sources,
        "tokens": used_tokens
    }