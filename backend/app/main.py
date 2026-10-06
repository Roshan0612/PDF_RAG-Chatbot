from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from app.retrieval import search_similar_chunks
from app.llm import generate_answer
from app.similarity import cosine_similarity

from app.database import Base, SessionLocal, engine
from app.embeddings import create_embedding
from app.models import (
    ChatMessage,
    ChatSession,
    Document,
    DocumentChunk
)
from app.conversation import (
    build_chat_history,
    build_retrieval_query
)
from pathlib import Path

from fastapi import UploadFile, File, HTTPException

from app.ingestion import create_chunks_from_pdf
import hashlib
from pydantic import BaseModel

from app.evaluation import evaluate_retrieval_case

from app.context_builder import build_context

from app.hybrid_retrieval import (
    hybrid_search
)
from typing import Literal

from app.retriever import retrieve_chunks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

Base.metadata.create_all(bind=engine)

class RetrievalEvaluationCase(BaseModel):
    query: str
    expected_document_id: int
    expected_page: int | None = None


class RetrievalEvaluationRequest(BaseModel):
    cases: list[RetrievalEvaluationCase]
    top_k: int = 3
    max_distance: float | None = None

class CreateChatSessionRequest(BaseModel):
    document_id: int | None = None


class ChatRequest(BaseModel):
    session_id: int
    message: str
    top_k: int = 5
    max_distance: float = 0.4
    max_context_tokens: int = 2000

    retrieval_strategy: Literal[
        "dense",
        "hybrid"
    ] = "hybrid"

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
        document = Document(
            filename="test-handbook.txt"
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        for text_content in texts:

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
    top_k: int = 5,
    max_distance: float = 0.4,
    document_id: int | None = None,
    max_context_tokens: int = 2000,
    retrieval_strategy: Literal[
        "dense",
        "hybrid"
    ] = "hybrid"
):
    results = await retrieve_chunks(
        query=question,
        top_k=top_k,
        max_distance=max_distance,
        document_id=document_id,
        strategy=retrieval_strategy
    )

    if not results:
        return {
            "question": question,
            "answer": (
                "I don't know based on "
                "the provided documents."
            ),
            "sources": []
        }

    context_data = build_context(
        results,
        max_tokens=max_context_tokens
    )

    if not context_data["context"]:
        return {
            "question": question,
            "answer": (
                "I don't know based on "
                "the provided documents."
            ),
            "sources": []
        }

    answer = await generate_answer(
        question=question,
        context=context_data["context"]
    )

    return {
        "question": question,
        "answer": answer,
        "retrieval_strategy": retrieval_strategy,
        "context_tokens": context_data["tokens"],
        "sources": context_data["sources"]
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


@app.post("/evaluate-retrieval")
async def evaluate_retrieval(
    request: RetrievalEvaluationRequest
):
    results = []

    for case in request.cases:
        result = await evaluate_retrieval_case(
            query=case.query,
            expected_document_id=case.expected_document_id,
            expected_page=case.expected_page,
            top_k=request.top_k,
            max_distance=request.max_distance
        )

        results.append(result)

    total_cases = len(results)

    hits = sum(
        1
        for result in results
        if result["hit"]
    )

    hit_rate = (
        hits / total_cases
        if total_cases
        else 0
    )

    mrr = (
        sum(
            result["reciprocal_rank"]
            for result in results
        ) / total_cases
        if total_cases
        else 0
    )

    return {
        "total_cases": total_cases,
        "hits": hits,
        "hit_rate": hit_rate,
        "mrr": mrr,
        "top_k": request.top_k,
        "max_distance": request.max_distance,
        "results": results
    }


@app.post("/chat/sessions")
def create_chat_session(
    request: CreateChatSessionRequest
):
    db = SessionLocal()

    try:
        if request.document_id is not None:
            document = db.get(
                Document,
                request.document_id
            )

            if document is None:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )

        session = ChatSession(
            document_id=request.document_id
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return {
            "session_id": session.id,
            "document_id": session.document_id,
            "created_at": session.created_at
        }

    finally:
        db.close()

@app.post("/chat")
async def chat(
    request: ChatRequest
):
    db = SessionLocal()

    try:
        session = db.get(
            ChatSession,
            request.session_id
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

        document_id = session.document_id

        previous_messages = (
            db.execute(
                select(ChatMessage)
                .where(
                    ChatMessage.session_id
                    == request.session_id
                )
                .order_by(
                    ChatMessage.id.desc()
                )
                .limit(6)
            )
            .scalars()
            .all()
        )

        previous_messages.reverse()

    finally:
        db.close()

    retrieval_query = build_retrieval_query(
        message=request.message,
        previous_messages=previous_messages
    )

    chat_history = build_chat_history(
        previous_messages
    )

    results = await retrieve_chunks(
        query=retrieval_query,
        top_k=request.top_k,
        max_distance=request.max_distance,
        document_id=document_id,
        strategy=request.retrieval_strategy
    )

    if results:
        context_data = build_context(
            results,
            max_tokens=request.max_context_tokens
        )
    else:
        context_data = {
            "context": "",
            "sources": [],
            "tokens": 0
        }

    if context_data["context"]:
        answer = await generate_answer(
            question=request.message,
            context=context_data["context"],
            chat_history=chat_history
        )
    else:
        answer = (
            "I don't know based on the provided documents."
        )

    db = SessionLocal()

    try:
        db.add(
            ChatMessage(
                session_id=request.session_id,
                role="user",
                content=request.message,
                
            )
        )

        db.add(
            ChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=answer,
                sources=context_data["sources"]
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    return {
        "session_id": request.session_id,
        "question": request.message,
        "answer": answer,
        "context_tokens": context_data["tokens"],
        "sources": context_data["sources"]
    }


@app.get(
    "/chat/sessions/{session_id}/messages"
)
def get_chat_messages(
    session_id: int
):
    db = SessionLocal()

    try:
        session = db.get(
            ChatSession,
            session_id
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

        messages = (
            db.execute(
                select(ChatMessage)
                .where(
                    ChatMessage.session_id
                    == session_id
                )
                .order_by(ChatMessage.id)
            )
            .scalars()
            .all()
        )

        return {
            "session_id": session.id,
            "document_id": session.document_id,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "sources": message.sources or [],
                    "created_at": message.created_at
                }
                for message in messages
            ]
        }

    finally:
        db.close()


@app.get("/chat/sessions")
def get_chat_sessions(
    document_id: int | None = None
):
    db = SessionLocal()

    try:
        message_count = (
            select(
                func.count(ChatMessage.id)
            )
            .where(
                ChatMessage.session_id
                == ChatSession.id
            )
            .correlate(ChatSession)
            .scalar_subquery()
        )

        statement = (
            select(
                ChatSession,
                message_count.label(
                    "message_count"
                )
            )
            .order_by(
                ChatSession.created_at.desc()
            )
        )

        if document_id is not None:
            statement = statement.where(
                ChatSession.document_id
                == document_id
            )

        results = db.execute(
            statement
        ).all()

        return {
            "sessions": [
                {
                    "id": session.id,
                    "document_id": session.document_id,
                    "created_at": session.created_at,
                    "message_count": count
                }
                for session, count in results
            ]
        }

    finally:
        db.close()

@app.delete("/chat/sessions/{session_id}")
def delete_chat_session(
    session_id: int
):
    db = SessionLocal()

    try:
        session = db.get(
            ChatSession,
            session_id
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

        db.delete(session)
        db.commit()

        return {
            "message": "Chat session deleted",
            "session_id": session_id
        }

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@app.get("/hybrid-search")
async def hybrid_search_endpoint(
    query: str,
    top_k: int = 5,
    document_id: int | None = None,
    max_distance: float | None = None
):
    results = await hybrid_search(
        query=query,
        top_k=top_k,
        document_id=document_id,
        max_distance=max_distance
    )

    return {
        "query": query,
        "results": [
            {
                "chunk_id":
                    result["chunk"].id,

                "document":
                    result[
                        "chunk"
                    ].document.filename,

                "page":
                    result[
                        "chunk"
                    ].page_number,

                "content":
                    result[
                        "chunk"
                    ].content,

                "rrf_score":
                    result["score"],

                "dense_rank":
                    result[
                        "dense_rank"
                    ],

                "keyword_rank":
                    result[
                        "keyword_rank"
                    ],

                "distance":
                    result[
                        "distance"
                    ]
            }
            for result in results
        ]
    }