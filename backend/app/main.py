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
    top_k: int = 3
):
    results = await search_similar_chunks(
        query=query,
        top_k=top_k
    )

    return {
        "query": query,
        "results": [
            {
                "chunk_id": chunk.id,
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
    top_k: int = 3
):
    # Step 1:
    # Find relevant chunks from the database
    results = await search_similar_chunks(
        query=question,
        top_k=top_k
    )

    # Step 2:
    # Extract the text from the retrieved chunks
    context_parts = []

    for chunk, distance in results:

        context_parts.append(
            f"[Source: {chunk.document.filename}, "
            f"Page: {chunk.page_number}]\n"
            f"{chunk.content}"
        )

    # Combine all chunks into one context
    context = "\n\n".join(context_parts)

    # Step 3:
    # Send question + retrieved context to the LLM
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

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / file.filename

    contents = await file.read()

    file_path.write_bytes(contents)

    chunks = create_chunks_from_pdf(
        str(file_path)
    )

    return {
        "filename": file.filename,
        "chunks": len(chunks),
        "preview": chunks[:3]
    }