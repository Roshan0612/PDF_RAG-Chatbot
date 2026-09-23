from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pgvector.sqlalchemy import Vector

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    filename: Mapped[str] = mapped_column(
        String(255)
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id")
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # nomic-embed-text produces our embedding vector.
    # We'll confirm the exact dimension from Ollama
    # before creating the database table.
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks"
    )