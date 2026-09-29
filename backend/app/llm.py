import httpx


OLLAMA_URL = "http://localhost:11434/api/chat"
LLM_MODEL = "llama3.2:3b"


async def generate_answer(
    question: str,
    context: str
) -> str:

    prompt = f"""
You are answering a question using retrieved document context.

Use ONLY the information provided in the context.

When you use information from a source, cite its source ID
directly in the answer using the format [S1], [S2], etc.

Do not cite a source unless it supports the statement.

If multiple sources support a statement, you may cite multiple
sources like [S1][S2].

If the answer cannot be found in the context, respond exactly:

"I don't know based on the provided documents."

Do not make up information.

Context:
--------------------
{context}
--------------------

Question:
{question}

Answer:
"""

    async with httpx.AsyncClient(timeout=120.0) as client:

        response = await client.post(
            OLLAMA_URL,
            json={
                "model": LLM_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
        )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]