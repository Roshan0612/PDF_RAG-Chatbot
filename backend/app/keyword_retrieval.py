from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import DocumentChunk


def search_keyword_chunks(
    query: str,
    top_k: int = 5,
    document_id: int | None = None
):
    db = SessionLocal()

    try:
        text_vector = func.to_tsvector(
            "english",
            DocumentChunk.content
        )

        search_query = func.websearch_to_tsquery(
            "english",
            query
        )

        rank = func.ts_rank_cd(
            text_vector,
            search_query
        )

        statement = (
            select(DocumentChunk)
            .options(
                joinedload(
                    DocumentChunk.document
                )
            )
            .add_columns(
                rank.label("rank")
            )
            .where(
                text_vector.op("@@")(
                    search_query
                )
            )
        )

        if document_id is not None:
            statement = statement.where(
                DocumentChunk.document_id
                == document_id
            )

        statement = (
            statement
            .order_by(
                rank.desc()
            )
            .limit(top_k)
        )

        return db.execute(
            statement
        ).all()

    finally:
        db.close()