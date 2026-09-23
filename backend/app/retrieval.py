from sqlalchemy import select

from app.database import SessionLocal
from app.embeddings import create_embedding
from app.models import DocumentChunk


async def search_similar_chunks(
    query: str,
    top_k: int = 3
):
    # Convert the user's question into an embedding
    query_embedding = await create_embedding(query)

    db = SessionLocal()

    try:
        # Calculate cosine distance between the question
        # vector and every stored chunk vector.
        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        # Sort by distance.
        #
        # Smaller distance = more similar
        #
        # limit(top_k) means we only return the best
        # few matching chunks.
        statement = (
            select(
                DocumentChunk,
                distance.label("distance")
            )
            .order_by(distance)
            .limit(top_k)
        )

        results = db.execute(statement).all()

        return results

    finally:
        db.close()