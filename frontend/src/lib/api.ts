import type {
  ChatMessage,
  ChatResponse,
  ChatSession,
  Document,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_URL is not configured"
  );
}

async function parseResponse<T>(
  response: Response
): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail || "Request failed"
    );
  }

  return response.json();
}

export async function getDocuments(): Promise<Document[]> {
  const response = await fetch(
    `${API_URL}/documents`
  );

  const data = await parseResponse<{
    documents: Document[];
  }>(response);

  return data.documents;
}

export async function uploadDocument(
  file: File
) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/ingest-pdf`,
    {
      method: "POST",
      body: formData,
    }
  );

  return parseResponse(response);
}

export async function deleteDocument(
  documentId: number
) {
  const response = await fetch(
    `${API_URL}/documents/${documentId}`,
    {
      method: "DELETE",
    }
  );

  return parseResponse(response);
}

export async function createChatSession(
  documentId: number | null
): Promise<number> {
  const response = await fetch(
    `${API_URL}/chat/sessions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        document_id: documentId,
      }),
    }
  );

  const data = await parseResponse<{
    session_id: number;
  }>(response);

  return data.session_id;
}

export async function sendChatMessage(
  sessionId: number,
  message: string
): Promise<ChatResponse> {
  const response = await fetch(
    `${API_URL}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        top_k: 3,
        max_distance: 0.4,
        max_context_tokens: 2000,
        retrieval_strategy: "hybrid",
      }),
    }
  );

  return parseResponse<ChatResponse>(
    response
  );
}

export async function getChatMessages(
  sessionId: number
): Promise<ChatMessage[]> {
  const response = await fetch(
    `${API_URL}/chat/sessions/${sessionId}/messages`
  );

  const data = await parseResponse<{
    messages: ChatMessage[];
  }>(response);

  return data.messages;
}


export async function getChatSessions(
  documentId: number
): Promise<ChatSession[]> {
  const response = await fetch(
    `${API_URL}/chat/sessions?document_id=${documentId}`
  );

  const data = await parseResponse<{
    sessions: ChatSession[];
  }>(response);

  return data.sessions;
}


export async function deleteChatSession(
  sessionId: number
) {
  const response = await fetch(
    `${API_URL}/chat/sessions/${sessionId}`,
    {
      method: "DELETE",
    }
  );

  return parseResponse(response);
}

