"use client";

import {
  useEffect,
  useState,
} from "react";

import ChatPanel from "@/components/ChatPanel";
import DocumentSidebar from "@/components/DocumentSidebar";

import {
  createChatSession,
  deleteChatSession,
  deleteDocument,
  getChatMessages,
  getChatSessions,
  getDocuments,
  sendChatMessage,
  uploadDocument,
} from "@/lib/api";

import type {
  ChatMessage,
  ChatSession,
  Document,
} from "@/types";


export default function Home() {
  const [documents, setDocuments] =
    useState<Document[]>([]);

  const [sessions, setSessions] =
    useState<ChatSession[]>([]);

  const [
    selectedDocument,
    setSelectedDocument,
  ] = useState<Document | null>(
    null
  );

  const [sessionId, setSessionId] =
    useState<number | null>(null);

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [uploading, setUploading] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);


  async function loadDocuments() {
    try {
      const data =
        await getDocuments();

      setDocuments(data);

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load documents"
      );
    }
  }


  async function loadSessions(
    documentId: number
  ) {
    const data =
      await getChatSessions(
        documentId
      );

    setSessions(data);

    return data;
  }


  async function openSession(
    session: ChatSession
  ) {
    try {
      setError(null);

      const history =
        await getChatMessages(
          session.id
        );

      setSessionId(
        session.id
      );

      setMessages(
        history
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load chat"
      );
    }
  }


  useEffect(() => {
    loadDocuments();
  }, []);


  async function handleUpload(
    file: File
  ) {
    try {
      setUploading(true);
      setError(null);

      await uploadDocument(
        file
      );

      await loadDocuments();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Upload failed"
      );

    } finally {
      setUploading(false);
    }
  }


  async function handleSelect(
    document: Document
  ) {
    try {
      setError(null);

      setSelectedDocument(
        document
      );

      setSessionId(null);
      setMessages([]);
      setSessions([]);

      const existingSessions =
        await loadSessions(
          document.id
        );

      if (
        existingSessions.length
      ) {
        await openSession(
          existingSessions[0]
        );

        return;
      }

      const newSessionId =
        await createChatSession(
          document.id
        );

      setSessionId(
        newSessionId
      );

      setMessages([]);

      await loadSessions(
        document.id
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to open document"
      );
    }
  }


  async function handleDelete(
    documentId: number
  ) {
    try {
      setError(null);

      await deleteDocument(
        documentId
      );

      if (
        selectedDocument?.id
        === documentId
      ) {
        setSelectedDocument(
          null
        );

        setSessionId(
          null
        );

        setMessages([]);

        setSessions([]);
      }

      await loadDocuments();

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Delete failed"
      );
    }
  }


  async function handleNewChat() {
    if (!selectedDocument) {
      return;
    }

    try {
      setError(null);

      const newSessionId =
        await createChatSession(
          selectedDocument.id
        );

      setSessionId(
        newSessionId
      );

      setMessages([]);

      await loadSessions(
        selectedDocument.id
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to create chat"
      );
    }
  }


  async function handleDeleteSession(
    chatSessionId: number
  ) {
    if (!selectedDocument) {
      return;
    }

    try {
      setError(null);

      await deleteChatSession(
        chatSessionId
      );

      const remaining =
        await loadSessions(
          selectedDocument.id
        );

      if (
        sessionId
        !== chatSessionId
      ) {
        return;
      }

      if (
        remaining.length
      ) {
        await openSession(
          remaining[0]
        );

        return;
      }

      const newSessionId =
        await createChatSession(
          selectedDocument.id
        );

      setSessionId(
        newSessionId
      );

      setMessages([]);

      await loadSessions(
        selectedDocument.id
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to delete chat"
      );
    }
  }


  async function handleSend(
    content: string
  ) {
    if (
      !sessionId ||
      !selectedDocument
    ) {
      return;
    }

    const userMessage: ChatMessage = {
      role: "user",
      content,
    };

    setMessages(
      (current) => [
        ...current,
        userMessage,
      ]
    );

    try {
      setLoading(true);
      setError(null);

      const response =
        await sendChatMessage(
          sessionId,
          content
        );

      const assistantMessage:
        ChatMessage = {
          role: "assistant",
          content:
            response.answer,
          sources:
            response.sources,
        };

      setMessages(
        (current) => [
          ...current,
          assistantMessage,
        ]
      );

      await loadSessions(
        selectedDocument.id
      );

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Chat request failed"
      );

    } finally {
      setLoading(false);
    }
  }


  return (
    <div className="flex h-screen bg-zinc-900 text-zinc-100">

      <DocumentSidebar
        documents={documents}
        sessions={sessions}
        selectedDocumentId={
          selectedDocument?.id ??
          null
        }
        selectedSessionId={
          sessionId
        }
        uploading={
          uploading
        }
        onUpload={
          handleUpload
        }
        onSelect={
          handleSelect
        }
        onDelete={
          handleDelete
        }
        onNewChat={
          handleNewChat
        }
        onSelectSession={
          openSession
        }
        onDeleteSession={
          handleDeleteSession
        }
      />


      <div className="flex min-w-0 flex-1 flex-col">

        {error && (
          <div className="bg-red-950 px-4 py-2 text-sm text-red-200">
            {error}
          </div>
        )}


        <ChatPanel
          document={
            selectedDocument
          }
          messages={
            messages
          }
          loading={
            loading
          }
          onSend={
            handleSend
          }
        />

      </div>

    </div>
  );
}