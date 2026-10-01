"use client";

import type {
  ChatSession,
  Document,
} from "@/types";

type Props = {
  documents: Document[];
  sessions: ChatSession[];

  selectedDocumentId: number | null;
  selectedSessionId: number | null;

  uploading: boolean;

  onUpload: (file: File) => void;

  onSelect: (
    document: Document
  ) => void;

  onDelete: (
    documentId: number
  ) => void;

  onNewChat: () => void;

  onSelectSession: (
    session: ChatSession
  ) => void;

  onDeleteSession: (
    sessionId: number
  ) => void;
};

export default function DocumentSidebar({
  documents,
  sessions,
  selectedDocumentId,
  selectedSessionId,
  uploading,
  onUpload,
  onSelect,
  onDelete,
  onNewChat,
  onSelectSession,
  onDeleteSession,
}: Props) {
  return (
    <aside className="flex h-screen w-80 flex-col border-r border-zinc-800 bg-zinc-950 p-4">

      <h1 className="mb-6 text-xl font-semibold">
        RAG Chat
      </h1>

      <label className="mb-5 cursor-pointer rounded-lg bg-white px-4 py-2 text-center text-sm font-medium text-black">
        {uploading
          ? "Uploading..."
          : "Upload PDF"}

        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          disabled={uploading}
          onChange={(event) => {
            const file =
              event.target.files?.[0];

            if (file) {
              onUpload(file);
            }

            event.target.value = "";
          }}
        />
      </label>

      <div className="flex flex-1 flex-col overflow-y-auto">

        {/* Documents */}

        <p className="mb-3 text-xs uppercase tracking-wider text-zinc-500">
          Documents
        </p>

        <div className="flex flex-col gap-2">
          {documents.map((document) => {
            const selected =
              selectedDocumentId
              === document.id;

            return (
              <div
                key={document.id}
                className={`rounded-lg border p-3 ${
                  selected
                    ? "border-zinc-500 bg-zinc-800"
                    : "border-zinc-800 bg-zinc-900"
                }`}
              >
                <button
                  onClick={() =>
                    onSelect(document)
                  }
                  className="w-full text-left"
                >
                  <p className="truncate text-sm font-medium">
                    {document.filename}
                  </p>

                  <p className="mt-1 text-xs text-zinc-500">
                    {document.chunks} chunks
                  </p>
                </button>

                <button
                  onClick={() =>
                    onDelete(document.id)
                  }
                  className="mt-3 text-xs text-red-400 hover:text-red-300"
                >
                  Delete
                </button>
              </div>
            );
          })}

          {!documents.length && (
            <p className="text-sm text-zinc-500">
              Upload a PDF to get started.
            </p>
          )}
        </div>

        {/* Chats */}

        {selectedDocumentId !== null && (
          <div className="mt-6 border-t border-zinc-800 pt-4">

            <div className="mb-3 flex items-center justify-between">

              <p className="text-xs uppercase tracking-wider text-zinc-500">
                Chats
              </p>

              <button
                onClick={onNewChat}
                className="text-xs text-zinc-300 hover:text-white"
              >
                + New
              </button>

            </div>

            <div className="flex flex-col gap-2">

              {sessions.map((session) => {
                const selected =
                  session.id
                  === selectedSessionId;

                return (
                  <div
                    key={session.id}
                    className={`rounded-lg border p-2 ${
                      selected
                        ? "border-zinc-500 bg-zinc-800"
                        : "border-zinc-800 bg-zinc-900"
                    }`}
                  >

                    <button
                      onClick={() =>
                        onSelectSession(
                          session
                        )
                      }
                      className="w-full text-left"
                    >
                      <p className="text-sm">
                        Chat #{session.id}
                      </p>

                      <p className="mt-1 text-xs text-zinc-500">
                        {session.message_count}{" "}
                        messages
                      </p>
                    </button>

                    <button
                      onClick={() =>
                        onDeleteSession(
                          session.id
                        )
                      }
                      className="mt-2 text-xs text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>

                  </div>
                );
              })}

              {!sessions.length && (
                <p className="text-xs text-zinc-500">
                  No previous chats.
                </p>
              )}

            </div>
          </div>
        )}

      </div>
    </aside>
  );
}