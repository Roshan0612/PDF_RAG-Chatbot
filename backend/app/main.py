from fastapi import FastAPI
from sqlalchemy import text
from app.retrieval import search_similar_chunks
from app.llm import generate_answer
from app.similarity import cosine_similarity

from app.database import Base, SessionLocal, engine
from app.embeddings import create_embedding
from app.models import Document, DocumentChunk
from pathlib import Path

from fastapi import UploadFile, File, HTTPException

from app.ingestion import create_chunks_from_pdf

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

    for chunk, distance in results:
        context_parts.append(
            f"[Source: {chunk.document.filename}, "
            f"Page: {chunk.page_number}]\n"
            f"{chunk.content}"
        )

    context = "\n\n".join(context_parts)

    answer = await generate_answer(
        question=question,
        context=context
    )

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "chunk_id": chunk.id,
                "document": chunk.document.filename,
                "page": chunk.page_number,
                "distance": float(distance)
            }
            for chunk, distance in results
        ]
    }

@app.post("/ingest-pdf")
async def ingest_pdf(
    file: UploadFile = File(...)
):
    # Only allow PDF files
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # Store uploaded PDFs locally for now
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    # Path(...).name prevents directory traversal
    safe_filename = Path(file.filename).name

    file_path = upload_dir / safe_filename

    # Read uploaded PDF
    contents = await file.read()

    # Save PDF locally
    file_path.write_bytes(contents)

    # PDF -> pages -> chunks
    chunks = create_chunks_from_pdf(
        str(file_path)
    )

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in the PDF"
        )

    db = SessionLocal()

    try:
        # -----------------------------------------
        # STEP 1: Create Document row
        # -----------------------------------------

        document = Document(
            filename=safe_filename
        )

        db.add(document)

        # Send INSERT to PostgreSQL so document.id
        # becomes available, but do NOT commit yet.
        db.flush()

        # -----------------------------------------
        # STEP 2: Process every chunk
        # -----------------------------------------

        for chunk_data in chunks:

            content = chunk_data["content"]
            page_number = chunk_data["page_number"]

            # Text -> embedding
            embedding = await create_embedding(
                content
            )

            # Create database chunk row
            document_chunk = DocumentChunk(
                document_id=document.id,
                content=content,
                page_number=page_number,
                embedding=embedding
            )

            db.add(document_chunk)

        # -----------------------------------------
        # STEP 3: Commit everything together
        # -----------------------------------------

        db.commit()

        return {
            "message": "PDF ingested successfully",
            "document_id": document.id,
            "filename": document.filename,
            "chunks": len(chunks)
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

@app.get("/documents")
def get_documents():
    db = SessionLocal()

    try:
        documents = db.query(Document).order_by(
            Document.id
        ).all()

        return {
            "documents": [
                {
                    "id": document.id,
                    "filename": document.filename,
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

        db.delete(document)
        db.commit()

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