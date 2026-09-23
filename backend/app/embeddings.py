import httpx


OLLAMA_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"


async def create_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": text
                }
            )
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to reach Ollama embedding API: {exc}") from exc

    try:
        response.raise_for_status()
        data = response.json()
    except (ValueError, httpx.HTTPStatusError) as exc:
        raise RuntimeError(f"Invalid response from Ollama embedding API: {exc}") from exc

    embeddings = data.get("embeddings") or data.get("embedding")

    if not embeddings:
        raise RuntimeError(f"Ollama embedding response missing data: {data}")

    if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], list):
        return embeddings[0]

    if isinstance(embeddings, list) and all(isinstance(value, (int, float)) for value in embeddings):
        return embeddings

    raise RuntimeError(f"Unexpected embedding format from Ollama: {data}")