"use client";

import { useEffect, useState } from "react";

import ChatPanel from "@/components/ChatPanel";
import DocumentSidebar from "@/components/DocumentSidebar";

import {
  createChatSession,
  deleteDocument,
  getDocuments,
  sendChatMessage,
  uploadDocument,
} from "@/lib/api";

import type {
  ChatMessage,
  Document,
} from "@/types";

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] =
    useState<Document | null>(null);

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
      const data = await getDocuments();

      setDocuments(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to load documents"
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

      await uploadDocument(file);

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

      const newSessionId =
        await createChatSession(
          document.id
        );

      setSelectedDocument(document);
      setSessionId(newSessionId);
      setMessages([]);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to create chat"
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
        selectedDocument?.id === documentId
      ) {
        setSelectedDocument(null);
        setSessionId(null);
        setMessages([]);
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

  async function handleSend(
    content: string
  ) {
    if (!sessionId) {
      return;
    }

    const userMessage: ChatMessage = {
      role: "user",
      content,
    };

    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    try {
      setLoading(true);
      setError(null);

      const response =
        await sendChatMessage(
          sessionId,
          content
        );

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
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
        selectedDocumentId={
          selectedDocument?.id ?? null
        }
        uploading={uploading}
        onUpload={handleUpload}
        onSelect={handleSelect}
        onDelete={handleDelete}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        {error && (
          <div className="bg-red-950 px-4 py-2 text-sm text-red-200">
            {error}
          </div>
        )}

        <ChatPanel
          document={selectedDocument}
          messages={messages}
          loading={loading}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}