import httpx


OLLAMA_URL = "http://localhost:11434/api/chat"
LLM_MODEL = "llama3.2:3b"


async def generate_answer(
    question: str,
    context: str
) -> str:

    prompt = f"""
You are a helpful assistant answering questions from a provided document.

Use ONLY the information provided in the context.

If the answer cannot be found in the context, say:
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