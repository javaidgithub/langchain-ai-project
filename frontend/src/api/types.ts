export type AgentId = "assistant" | "rag" | "research";

export interface ProviderInfo {
  id: string;
  label: string;
  models: string[];
  needs_key: boolean;
  configured: boolean;
  docs_url: string;
}
export interface ToolInfo {
  name: string;
  description: string;
  category: string;
  requires_approval: boolean;
}
export interface AgentInfo {
  id: AgentId;
  label: string;
  description: string;
}
export interface ThreadMeta {
  id: string;
  title: string;
  agent: AgentId;
  created_at: string;
  updated_at: string;
}
export interface Source {
  index: number;
  source: string;
  page: number | null;
  snippet: string;
}
export interface Usage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  llm_calls: number;
}
export interface ToolCallRequest {
  id: string;
  name: string;
  args: Record<string, unknown>;
  needs_approval: boolean;
}

export type InterruptValue =
  | { type: "tool_approval"; message: string; tool_calls: ToolCallRequest[] }
  | { type: "plan_approval"; message: string; plan: string[] };

export interface Decision {
  action: "approve" | "reject" | "edit" | "cancel";
  edited_args?: Record<string, Record<string, unknown>>;
  feedback?: string;
  plan?: string[];
}

export type StreamEvent =
  | { type: "start"; thread_id: string }
  | { type: "step"; node: string }
  | { type: "token"; content: string; node?: string }
  | { type: "reasoning"; content: string }
  | { type: "tool_call"; id: string; name: string; args: Record<string, unknown> }
  | { type: "tool_result"; tool_call_id: string; name: string; content: string; status: string }
  | { type: "context"; summary: string }
  | { type: "plan"; plan: string[] }
  | { type: "sources"; sources: Source[] }
  | ({ type: "usage" } & Usage)
  | { type: "interrupt"; id: string; value: InterruptValue }
  | { type: "error"; message: string }
  | { type: "done"; interrupted: boolean };

export interface ServerMessage {
  id: string | null;
  role: "user" | "assistant" | "tool";
  content: string;
  tool_calls?: { id: string; name: string; args: Record<string, unknown> }[];
  tool_call_id?: string;
  status?: string;
}
export interface ThreadDetail extends ThreadMeta {
  messages: ServerMessage[];
  summary: string | null;
  interrupts: { id: string; value: InterruptValue }[];
}
export interface ChainInfo {
  id: string;
  description: string;
  fields: Record<string, string>;
}
export interface KnowledgeDoc {
  name: string;
  chunks: number;
}
export interface MemoryItem {
  id: string;
  content: string;
}
