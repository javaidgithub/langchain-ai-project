import { BookOpen, FlaskConical, MessageSquare, Plus, Trash2, X } from "lucide-react";
import { newChat, openThread, removeThread } from "../hooks/chatActions";
import { useCatalog } from "../store/catalog";
import { type View, useChat } from "../store/chat";
import { useSettings } from "../store/settings";

const NAV: { id: View; label: string; icon: typeof MessageSquare }[] = [
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "knowledge", label: "Documents", icon: BookOpen },
  { id: "chains", label: "Chains", icon: FlaskConical },
];

export function Sidebar() {
  const { view, threads, activeThreadId, sidebarOpen } = useChat();
  const agent = useSettings((s) => s.agent);
  const patch = useSettings((s) => s.patch);
  const agents = useCatalog((s) => s.agents);
  const locked = activeThreadId !== null;

  return (
    <aside className={`sidebar ${sidebarOpen ? "is-open" : ""}`} aria-label="Navigation">
      <div className="brand">
        <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden><rect width="32" height="32" rx="8" fill="var(--primary)" /><path d="M10 7v18M10 11h12M10 21h8" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" fill="none" /><circle cx="22" cy="21" r="3.2" fill="var(--hold)" /></svg>
        <span>AI Workbench</span>
        <button className="icon-btn only-narrow" aria-label="Close menu" onClick={() => useChat.setState({ sidebarOpen: false })}><X size={18} /></button>
      </div>

      <nav className="nav" aria-label="Sections">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} className={view === id ? "is-active" : ""} aria-current={view === id ? "page" : undefined}
            onClick={() => useChat.setState({ view: id, sidebarOpen: false })}>
            <Icon size={16} aria-hidden /> {label}
          </button>
        ))}
      </nav>

      <button className="btn btn-primary new-chat" onClick={newChat}><Plus size={16} aria-hidden /> New chat</button>

      <div className="agent-switch" role="radiogroup" aria-label="Agent">
        {agents.map((a) => (
          <button key={a.id} role="radio" aria-checked={agent === a.id} disabled={locked && agent !== a.id}
            title={locked ? "Start a new chat to switch agents" : a.description}
            className={agent === a.id ? "is-active" : ""} onClick={() => patch({ agent: a.id })}>
            {a.label}
          </button>
        ))}
      </div>

      <h2 className="side-heading">Recent</h2>
      <ul className="threads">
        {threads.length === 0 && <li className="muted pad">Conversations you start will appear here.</li>}
        {threads.map((t) => (
          <li key={t.id} className={t.id === activeThreadId ? "is-active" : ""}>
            <button className="thread-link" onClick={() => void openThread(t.id)}>
              <span className="thread-title">{t.title}</span>
              <span className="thread-agent">{agents.find((a) => a.id === t.agent)?.label ?? t.agent}</span>
            </button>
            <button className="icon-btn thread-del" aria-label={`Delete ${t.title}`} onClick={() => void removeThread(t.id)}><Trash2 size={14} /></button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
