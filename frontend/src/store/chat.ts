import { create } from "zustand";
import type { InterruptValue, Source, ThreadMeta, Usage } from "../api/types";

export type ToolStatus = "running" | "done" | "error" | "held" | "rejected";

export type Part =
  | { kind: "text"; text: string }
  | { kind: "reasoning"; text: string }
  | { kind: "tool"; id: string; name: string; args: Record<string, unknown>; status: ToolStatus; result?: string }
  | { kind: "step"; node: string }
  | { kind: "context"; summary: string }
  | { kind: "plan"; plan: string[] };

export interface Msg {
  id: string;
  role: "user" | "assistant";
  parts: Part[];
  sources?: Source[];
  usage?: Usage;
  error?: string;
}

export type View = "chat" | "knowledge" | "chains";

interface ChatState {
  view: View;
  threads: ThreadMeta[];
  activeThreadId: string | null;
  messages: Msg[];
  interrupt: InterruptValue | null;
  streaming: boolean;
  sidebarOpen: boolean;
  inspectorOpen: boolean;
}

export const useChat = create<ChatState>(() => ({
  view: "chat",
  threads: [],
  activeThreadId: null,
  messages: [],
  interrupt: null,
  streaming: false,
  sidebarOpen: false,
  inspectorOpen: false,
}));
