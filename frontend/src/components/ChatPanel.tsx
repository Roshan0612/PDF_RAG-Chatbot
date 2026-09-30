"use client";

import { FormEvent, useState } from "react";

import type {
  ChatMessage,
  Document,
} from "@/types";

type Props = {
  document: Document | null;
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => void;
};

export default function ChatPanel({
  document,
  messages,
  loading,
  onSend,
}: Props) {
  const [message, setMessage] = useState("");

  function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const value = message.trim();

    if (!value || loading) {
      return;
    }

    onSend(value);
    setMessage("");
  }

  return (
    <main className="flex h-screen flex-1 flex-col bg-zinc-900">
      <header className="border-b border-zinc-800 px-6 py-4">
        <h2 className="font-medium">
          {document
            ? document.filename
            : "Select a document"}
        </h2>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {!messages.length && (
          <div className="flex h-full items-center justify-center">
            <p className="text-zinc-500">
              {document
                ? "Ask something about this document."
                : "Select a document to start chatting."}
            </p>
          </div>
        )}

        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          {messages.map((message, index) => (
            <div
              key={message.id ?? index}
              className={
                message.role === "user"
                  ? "ml-auto max-w-[75%]"
                  : "mr-auto max-w-[85%]"
              }
            >
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                  message.role === "user"
                    ? "bg-white text-black"
                    : "bg-zinc-800 text-zinc-100"
                }`}
              >
                {message.content}
              </div>

              {message.sources?.length ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {message.sources.map(
                    (source) => (
                      <span
                        key={source.source_id}
                        className="rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-400"
                      >
                        {source.source_id} · Page{" "}
                        {source.page ?? "N/A"}
                      </span>
                    )
                  )}
                </div>
              ) : null}
            </div>
          ))}

          {loading && (
            <p className="text-sm text-zinc-500">
              Thinking...
            </p>
          )}
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-zinc-800 p-4"
      >
        <div className="mx-auto flex max-w-3xl gap-3">
          <input
            value={message}
            disabled={!document || loading}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            placeholder={
              document
                ? "Ask about this document..."
                : "Select a document first"
            }
            className="flex-1 rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-sm outline-none focus:border-zinc-500"
          />

          <button
            disabled={
              !document ||
              !message.trim() ||
              loading
            }
            className="rounded-xl bg-white px-5 py-3 text-sm font-medium text-black disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </main>
  );
}