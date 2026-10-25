import type {
  AgentInfo, ChainInfo, KnowledgeDoc, MemoryItem, ProviderInfo, Source, StreamEvent,
  ThreadDetail, ThreadMeta, ToolInfo,
} from "./types";

const BASE: string = import.meta.env.VITE_API_URL || "/api";
const TOKEN: string | undefined = import.meta.env.VITE_API_TOKEN || undefined;

function headers(extra?: HeadersInit): HeadersInit {
  return { ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}), ...extra };
}

async function failure(res: Response): Promise<Error> {
  let detail = res.statusText || `Request failed (${res.status})`;
  try {
    const body = await res.json();
    detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
  } catch {
    /* body was not JSON */
  }
  return new Error(detail);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(BASE + path, { ...init, headers: headers(init.headers) });
  if (!res.ok) throw await failure(res);
  return (res.status === 204 ? undefined : await res.json()) as T;
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export interface ModelBody {
  provider: string;
  model: string;
  temperature: number;
  api_key: string | null;
}

export const api = {
  models: () => request<ProviderInfo[]>("/models"),
  tools: () => request<ToolInfo[]>("/tools"),
  agents: () => request<AgentInfo[]>("/agents"),
  threads: () => request<ThreadMeta[]>("/threads"),
  thread: (id: string) => request<ThreadDetail>(`/threads/${id}`),
  deleteThread: (id: string) => request<void>(`/threads/${id}`, { method: "DELETE" }),
  documents: () => request<KnowledgeDoc[]>("/rag/documents"),
  deleteDocument: (name: string) => request<void>(`/rag/documents/${encodeURIComponent(name)}`, { method: "DELETE" }),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<KnowledgeDoc>("/rag/upload", { method: "POST", body: form });
  },
  ragQuery: (question: string, model: ModelBody) =>
    request<{ answer: string; sources: Source[] }>("/rag/query", json({ question, model })),
  chains: () => request<ChainInfo[]>("/chains"),
  runChain: (name: string, inputs: Record<string, string>, model: ModelBody) =>
    request<{ output: unknown }>(`/chains/${name}`, json({ inputs, model })),
  memories: () => request<MemoryItem[]>("/memory"),
  deleteMemory: (id: string) => request<void>(`/memory/${id}`, { method: "DELETE" }),
};

/** POST and consume a Server-Sent Events stream (EventSource cannot POST). */
export async function streamSSE(
  path: string,
  body: unknown,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(BASE + path, { ...json(body), headers: headers({ "Content-Type": "application/json" }), signal });
  if (!res.ok || !res.body) throw await failure(res);

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const data = frame.split("\n").filter((l) => l.startsWith("data: ")).map((l) => l.slice(6)).join("\n");
      if (data) onEvent(JSON.parse(data) as StreamEvent);
    }
  }
}
