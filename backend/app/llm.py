import httpx


OLLAMA_URL = "http://localhost:11434/api/chat"
LLM_MODEL = "llama3.2:3b"


async def generate_answer(
    question: str,
    context: str,
    chat_history: str = ""
) -> str:

    prompt = f"""

You are answering a question using retrieved document context.

Use ONLY the information provided in the retrieved context
for factual claims about the documents.

Conversation history is provided only to understand follow-up
questions and references from the user.

When you use information from a source, cite its source ID
using [S1], [S2], etc.

Do not cite a source unless it supports the statement.

If the answer cannot be found in the retrieved context, respond:

"I don't know based on the provided documents."

Do not make up information.

Conversation history:
--------------------
{chat_history}
--------------------

Retrieved context:
--------------------
{context}
--------------------

Current question:
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