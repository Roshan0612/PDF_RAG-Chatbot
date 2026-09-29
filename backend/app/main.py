from fastapi import FastAPI
from sqlalchemy import select,text
from app.retrieval import search_similar_chunks
from app.llm import generate_answer
from app.similarity import cosine_similarity

from app.database import Base, SessionLocal, engine
from app.embeddings import create_embedding
from app.models import Document, DocumentChunk
from pathlib import Path

from fastapi import UploadFile, File, HTTPException

from app.ingestion import create_chunks_from_pdf
import hashlib

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {
        "message": "RAG Chatbot API is running"
    }


@app.post("/embed")
async def embed(text: str):
    vector = await create_embedding(text)

    return {
        "dimensions": len(vector),
        "embedding": vector
    }

@app.post("/compare")
async def compare(
    text_a: str,
    text_b: str
):
    embedding_a = await create_embedding(text_a)
    embedding_b = await create_embedding(text_b)

    score = cosine_similarity(
        embedding_a,
        embedding_b
    )

    return {
        "similarity": score
    }


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "result": value
    }

@app.post("/test-document")
async def create_test_document():

    # Temporary test data.
    # Later, these chunks will come from a PDF.
    texts = [
        "Employees receive 24 paid leaves every year.",
        "Employees can apply for sick leave through the HR portal.",
        "The company provides health insurance to all full-time employees.",
        "Employees receive a monthly transportation allowance."
    ]

    db = SessionLocal()

    try:
        # Create the document
        document = Document(
            filename="test-handbook.txt"
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Create one database row for every chunk
        for text_content in texts:

            # Convert text → embedding vector
            vector = await create_embedding(text_content)

            chunk = DocumentChunk(
                document_id=document.id,
                content=text_content,
                embedding=vector
            )

            db.add(chunk)

        db.commit()

        return {
            "message": "Test document created",
            "document_id": document.id,
            "chunks": len(texts)
        }

    finally:
        db.close()

@app.get("/search")
async def search(
    query: str,
    top_k: int = 3,
    max_distance: float | None = None,
    document_id: int | None = None
):
    results = await search_similar_chunks(
        query=query,
        top_k=top_k,
        max_distance=max_distance,
        document_id=document_id
    )

    return {
        "query": query,
        "results": [
            {
                "chunk_id": chunk.id,
                "document": chunk.document.filename,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "distance": float(distance)
            }
            for chunk, distance in results
        ]
    }
@app.get("/rag")
async def rag(
    question: str,
    top_k: int = 3,
    max_distance: float = 0.4,
    document_id: int | None = None
):
    results = await search_similar_chunks(
        query=question,
        top_k=top_k,
        max_distance=max_distance,
        document_id=document_id
    )

    if not results:
        return {
            "question": question,
            "answer": "I don't know based on the provided documents.",
            "sources": []
        }

    context_parts = []
    sources = []

    for index, (chunk, distance) in enumerate(
        results,
        start=1
    ):
        source_id = f"S{index}"

        context_parts.append(
            f"[{source_id}]\n"
            f"Document: {chunk.document.filename}\n"
            f"Page: {chunk.page_number}\n"
            f"{chunk.content}"
        )

        sources.append({
            "source_id": source_id,
            "chunk_id": chunk.id,
            "document": chunk.document.filename,
            "page": chunk.page_number,
            "distance": float(distance)
        })

    context = "\n\n".join(
        context_parts
    )

    answer = await generate_answer(
        question=question,
        context=context
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }

@app.post("/ingest-pdf")
async def ingest_pdf(
    file: UploadFile = File(...)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    safe_filename = Path(
        file.filename or "document.pdf"
    ).name

    contents = await file.read()

    file_hash = hashlib.sha256(
        contents
    ).hexdigest()

    db = SessionLocal()

    file_path = None

    try:
        existing_document = db.execute(
            select(Document).where(
                Document.file_hash == file_hash
            )
        ).scalar_one_or_none()

        if existing_document:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Document already exists with "
                    f"id {existing_document.id}"
                )
            )

        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        storage_name = (
            f"{file_hash[:12]}_{safe_filename}"
        )

        file_path = upload_dir / storage_name

        file_path.write_bytes(contents)

        chunks = create_chunks_from_pdf(
            str(file_path)
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No extractable text found in PDF"
            )

        document = Document(
            filename=safe_filename,
            storage_name=storage_name,
            file_hash=file_hash,
            file_size=len(contents),
            content_type=file.content_type
        )

        db.add(document)
        db.flush()

        for chunk_index, chunk_data in enumerate(
            chunks,
            start=1
        ):
            embedding = await create_embedding(
                chunk_data["content"]
            )

            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk_index,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                embedding=embedding
            )

            db.add(document_chunk)

        db.commit()
        db.refresh(document)

        return {
            "message": "PDF ingested successfully",
            "document_id": document.id,
            "filename": document.filename,
            "chunks": len(chunks),
            "file_size": document.file_size
        }

    except HTTPException:
        db.rollback()

        if file_path and file_path.exists():
            file_path.unlink()

        raise

    except Exception:
        db.rollback()

        if file_path and file_path.exists():
            file_path.unlink()

        raise

    finally:
        db.close()

@app.get("/documents")
def get_documents():
    db = SessionLocal()

    try:
        documents = db.execute(
            select(Document)
            .order_by(Document.id)
        ).scalars().all()

        return {
            "documents": [
                {
                    "id": document.id,
                    "filename": document.filename,
                    "file_size": document.file_size,
                    "content_type": document.content_type,
                    "created_at": document.created_at,
                    "chunks": len(document.chunks)
                }
                for document in documents
            ]
        }

    finally:
        db.close()

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int
):
    db = SessionLocal()

    try:
        document = db.get(
            Document,
            document_id
        )

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        filename = document.filename
        storage_name = document.storage_name

        db.delete(document)
        db.commit()

        if storage_name:
            file_path = (
                Path("uploads") / storage_name
            )

            if file_path.exists():
                file_path.unlink()

        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "filename": filename
        }

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()