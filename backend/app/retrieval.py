from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.embeddings import create_embedding
from app.models import DocumentChunk


async def search_similar_chunks(
    query: str,
    top_k: int = 3,
    max_distance: float | None = None,
    document_id: int | None = None
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
        )

        if document_id is not None:
            statement = statement.where(
                DocumentChunk.document_id == document_id
            )

        if max_distance is not None:
            statement = statement.where(
                distance <= max_distance
            )

        statement = (
            statement
            .order_by(distance)
            .limit(top_k)
        )

        return db.execute(statement).all()

    finally:
        db.close()