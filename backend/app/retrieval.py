from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.embeddings import create_embedding
from app.models import DocumentChunk


async def search_similar_chunks(
    query: str,
    top_k: int = 3
):
    query_embedding = await create_embedding(query)

    db = SessionLocal()

    try:

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        statement = (
            select(DocumentChunk)
            .options(
                joinedload(DocumentChunk.document)
            )
            .add_columns(
                distance.label("distance")
            )
            .order_by(distance)
            .limit(top_k)
        )

        results = db.execute(statement).all()

        return results

    finally:
        db.close()