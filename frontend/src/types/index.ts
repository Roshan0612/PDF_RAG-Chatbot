export type Document = {
  id: number;
  filename: string;
  file_size: number | null;
  content_type: string | null;
  created_at: string | null;
  chunks: number;
};

export type Source = {
  source_id: string;
  chunk_id: number;
  document: string;
  page: number | null;

  distance: number | null;
  rrf_score?: number | null;

  dense_rank?: number | null;
  keyword_rank?: number | null;
};

export type ChatMessage = {
  id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
  sources?: Source[];
};

export type ChatResponse = {
  session_id: number;
  question: string;
  answer: string;
  context_tokens: number;
  sources: Source[];
};

export type ChatSession = {
  id: number;
  document_id: number | null;
  created_at: string;
  message_count: number;
};