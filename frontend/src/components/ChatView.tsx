import { PanelLeft, SlidersHorizontal } from "lucide-react";
import { useEffect, useRef } from "react";
import { send } from "../hooks/chatActions";
import { useCatalog } from "../store/catalog";
import { useChat } from "../store/chat";
import { useSettings } from "../store/settings";
import { ApprovalGate } from "./ApprovalGate";
import { Composer } from "./Composer";
import { MessageView } from "./MessageView";

const SUGGESTIONS: Record<string, string[]> = {
  assistant: [
    "What is 18% of 2,450 plus 12% of 980?",
    "Search the web for the latest LangGraph release notes and summarize them",
    "Email team@example.com a short summary of today's priorities",
  ],
  rag: ["Summarize the main points of my documents", "What do my documents say about pricing?"],
  research: ["Compare vector databases for production RAG", "How do transformers handle long context?"],
};

export function ChatView() {
  const messages = useChat((s) => s.messages);
  const streaming = useChat((s) => s.streaming);
  const interrupt = useChat((s) => s.interrupt);
  const threadTitle = useChat((s) => s.threads.find((t) => t.id === s.activeThreadId)?.title);
  const agent = useSettings((s) => s.agent);
  const provider = useSettings((s) => s.provider);
  const model = useSettings((s) => s.model);
  const agents = useCatalog((s) => s.agents);
  const endRef = useRef<HTMLDivElement>(null);
  const scroller = useRef<HTMLDivElement>(null);

  // Follow the stream, but don't yank the view if the reader scrolled up.
  useEffect(() => {
    const el = scroller.current;
    if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 160) endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, interrupt]);

  const info = agents.find((a) => a.id === agent);

  return (
    <div className="chat">
      <header className="topbar">
        <button className="icon-btn only-narrow" aria-label="Open conversations" onClick={() => useChat.setState({ sidebarOpen: true })}>
          <PanelLeft size={18} />
        </button>
        <div className="topbar-title">
          <h1>{threadTitle ?? "New conversation"}</h1>
          <p>{info?.label ?? agent} · {provider} / {model}</p>
        </div>
        <button className="icon-btn only-medium" aria-label="Open settings" onClick={() => useChat.setState({ inspectorOpen: true })}>
          <SlidersHorizontal size={18} />
        </button>
      </header>

      <div className="scroller" ref={scroller}>
        <div className="thread">
          {messages.length === 0 ? (
            <div className="empty">
              <h2>{info?.label ?? "Assistant"}</h2>
              <p>{info?.description}</p>
              <ul>
                {(SUGGESTIONS[agent] ?? []).map((s) => (
                  <li key={s}><button className="suggestion" onClick={() => void send(s)}>{s}</button></li>
                ))}
              </ul>
            </div>
          ) : (
            messages.map((m, i) => <MessageView key={m.id} msg={m} live={streaming && i === messages.length - 1} />)
          )}
          {interrupt && <ApprovalGate key={JSON.stringify(interrupt)} value={interrupt} />}
          <div ref={endRef} />
        </div>
      </div>
      <Composer />
    </div>
  );
}
