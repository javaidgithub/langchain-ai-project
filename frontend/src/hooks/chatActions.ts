import { api, streamSSE } from "../api/client";
import type { Decision, InterruptValue, ServerMessage, StreamEvent, ThreadDetail } from "../api/types";
import { isTraceStep } from "../lib/labels";
import { type Msg, type Part, useChat } from "../store/chat";
import { useSettings } from "../store/settings";

let controller: AbortController | null = null;
const uid = () => crypto.randomUUID();

const chat = {
  get: useChat.getState,
  set: useChat.setState,
};

/** Options that tell the backend which agent, model and tools to use for this run. */
function runOptions() {
  const s = useSettings.getState();
  return {
    agent: s.agent,
    model: { provider: s.provider, model: s.model, temperature: s.temperature, api_key: s.apiKeys[s.provider] || null },
    enabled_tools: s.enabledTools,
    require_approval: s.requireApproval,
    system_prompt: s.systemPrompt.trim() || null,
  };
}

function updateLastAssistant(fn: (m: Msg) => Msg) {
  chat.set((state) => {
    const messages = state.messages.slice();
    const i = messages.length - 1;
    if (i >= 0 && messages[i].role === "assistant") messages[i] = fn(messages[i]);
    return { messages };
  });
}

const withPart = (m: Msg, part: Part): Msg => ({ ...m, parts: [...m.parts, part] });

function appendText(m: Msg, kind: "text" | "reasoning", text: string): Msg {
  const parts = m.parts.slice();
  const last = parts[parts.length - 1];
  if (last && last.kind === kind) parts[parts.length - 1] = { ...last, text: last.text + text };
  else parts.push({ kind, text });
  return { ...m, parts };
}

function patchTool(m: Msg, id: string, patch: Partial<Extract<Part, { kind: "tool" }>>): Msg {
  return { ...m, parts: m.parts.map((p) => (p.kind === "tool" && p.id === id ? { ...p, ...patch } : p)) };
}

function applyEvent(e: StreamEvent) {
  switch (e.type) {
    case "start":
      if (!chat.get().activeThreadId) chat.set({ activeThreadId: e.thread_id });
      break;
    case "step":
      if (isTraceStep(e.node)) updateLastAssistant((m) => withPart(m, { kind: "step", node: e.node }));
      break;
    case "token":
      updateLastAssistant((m) => appendText(m, "text", e.content));
      break;
    case "reasoning":
      updateLastAssistant((m) => appendText(m, "reasoning", e.content));
      break;
    case "tool_call":
      updateLastAssistant((m) => withPart(m, { kind: "tool", id: e.id, name: e.name, args: e.args, status: "running" }));
      break;
    case "tool_result": {
      const rejected = e.content.startsWith("The user rejected");
      updateLastAssistant((m) =>
        patchTool(m, e.tool_call_id, {
          status: rejected ? "rejected" : e.status === "error" ? "error" : "done",
          result: e.content,
        }),
      );
      break;
    }
    case "context":
      updateLastAssistant((m) => withPart(m, { kind: "context", summary: e.summary }));
      break;
    case "plan":
      updateLastAssistant((m) => withPart(m, { kind: "plan", plan: e.plan }));
      break;
    case "sources":
      updateLastAssistant((m) => ({ ...m, sources: e.sources }));
      break;
    case "usage": {
      const { type: _type, ...usage } = e;
      updateLastAssistant((m) => ({ ...m, usage }));
      break;
    }
    case "interrupt":
      holdInterrupt(e.value);
      break;
    case "error":
      updateLastAssistant((m) => ({ ...m, error: e.message }));
      break;
    case "done":
      break;
  }
}

function holdInterrupt(value: InterruptValue) {
  chat.set({ interrupt: value });
  if (value.type === "tool_approval") {
    const ids = new Set(value.tool_calls.map((c) => c.id));
    updateLastAssistant((m) => ({
      ...m,
      parts: m.parts.map((p) => (p.kind === "tool" && ids.has(p.id) ? { ...p, status: "held" as const } : p)),
    }));
  }
}

async function run(path: string, body: unknown) {
  controller = new AbortController();
  chat.set({ streaming: true });
  try {
    await streamSSE(path, body, applyEvent, controller.signal);
  } catch (err) {
    if ((err as Error).name !== "AbortError") {
      updateLastAssistant((m) => ({ ...m, error: (err as Error).message }));
    }
  } finally {
    controller = null;
    chat.set({ streaming: false });
    void refreshThreads();
  }
}

export async function send(message: string) {
  const text = message.trim();
  if (!text || chat.get().streaming || chat.get().interrupt) return;
  chat.set((s) => ({
    messages: [
      ...s.messages,
      { id: uid(), role: "user", parts: [{ kind: "text", text }] },
      { id: uid(), role: "assistant", parts: [] },
    ],
  }));
  await run("/chat/stream", { ...runOptions(), thread_id: chat.get().activeThreadId, message: text });
}

/** Continue a run that paused for human input. */
export async function resume(decision: Decision) {
  const threadId = chat.get().activeThreadId;
  if (!threadId || chat.get().streaming) return;
  chat.set({ interrupt: null });
  if (decision.action === "approve" || decision.action === "edit") {
    updateLastAssistant((m) => ({
      ...m,
      parts: m.parts.map((p) => (p.kind === "tool" && p.status === "held" ? { ...p, status: "running" as const } : p)),
    }));
  }
  await run("/chat/resume", { ...runOptions(), thread_id: threadId, decision });
}

export function stop() {
  controller?.abort();
}

export async function refreshThreads() {
  try {
    chat.set({ threads: await api.threads() });
  } catch {
    /* sidebar is non-critical */
  }
}

export function newChat() {
  controller?.abort();
  chat.set({ activeThreadId: null, messages: [], interrupt: null, streaming: false, view: "chat", sidebarOpen: false });
}

/** Rebuild UI messages from the server's normalized history. */
export function toMessages(history: ServerMessage[]): Msg[] {
  const out: Msg[] = [];
  for (const m of history) {
    if (m.role === "user") {
      out.push({ id: m.id ?? uid(), role: "user", parts: [{ kind: "text", text: m.content }] });
      continue;
    }
    let current = out[out.length - 1];
    if (!current || current.role !== "assistant") {
      current = { id: m.id ?? uid(), role: "assistant", parts: [] };
      out.push(current);
    }
    if (m.role === "assistant") {
      if (m.content) current.parts.push({ kind: "text", text: m.content });
      for (const c of m.tool_calls ?? []) {
        current.parts.push({ kind: "tool", id: c.id, name: c.name, args: c.args, status: "running" });
      }
    } else {
      const part = current.parts.find((p) => p.kind === "tool" && p.id === m.tool_call_id);
      if (part && part.kind === "tool") {
        part.result = m.content;
        part.status = m.content.startsWith("The user rejected") ? "rejected" : m.status === "error" ? "error" : "done";
      }
    }
  }
  return out;
}

export async function openThread(id: string) {
  controller?.abort();
  const detail: ThreadDetail = await api.thread(id);
  useSettings.getState().patch({ agent: detail.agent });
  chat.set({ activeThreadId: id, messages: toMessages(detail.messages), interrupt: null, view: "chat", sidebarOpen: false });
  if (detail.interrupts[0]) holdInterrupt(detail.interrupts[0].value);
}

export async function removeThread(id: string) {
  await api.deleteThread(id);
  if (chat.get().activeThreadId === id) newChat();
  await refreshThreads();
}
