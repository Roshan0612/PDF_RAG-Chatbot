"use client";

import type { Document } from "@/types";

type Props = {
  documents: Document[];
  selectedDocumentId: number | null;
  uploading: boolean;
  onUpload: (file: File) => void;
  onSelect: (document: Document) => void;
  onDelete: (documentId: number) => void;
};

export default function DocumentSidebar({
  documents,
  selectedDocumentId,
  uploading,
  onUpload,
  onSelect,
  onDelete,
}: Props) {
  return (
    <aside className="flex h-screen w-80 flex-col border-r border-zinc-800 bg-zinc-950 p-4">
      <h1 className="mb-6 text-xl font-semibold">
        RAG Chat
      </h1>

      <label className="mb-5 cursor-pointer rounded-lg bg-white px-4 py-2 text-center text-sm font-medium text-black">
        {uploading ? "Uploading..." : "Upload PDF"}

        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          disabled={uploading}
          onChange={(event) => {
            const file = event.target.files?.[0];

            if (file) {
              onUpload(file);
            }

            event.target.value = "";
          }}
        />
      </label>

      <p className="mb-3 text-xs uppercase tracking-wider text-zinc-500">
        Documents
      </p>

      <div className="flex flex-1 flex-col gap-2 overflow-y-auto">
        {documents.map((document) => {
          const selected =
            selectedDocumentId === document.id;

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
                onClick={() => onSelect(document)}
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
                onClick={() => onDelete(document.id)}
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
    </aside>
  );
}