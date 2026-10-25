import { useEffect } from "react";
import { ChainsView } from "./components/ChainsView";
import { ChatView } from "./components/ChatView";
import { Inspector } from "./components/Inspector";
import { KnowledgeView } from "./components/KnowledgeView";
import { Sidebar } from "./components/Sidebar";
import { refreshThreads } from "./hooks/chatActions";
import { useCatalog } from "./store/catalog";
import { useChat } from "./store/chat";

export default function App() {
  const view = useChat((s) => s.view);
  const open = useChat((s) => s.sidebarOpen || s.inspectorOpen);
  const backendError = useCatalog((s) => s.backendError);
  const load = useCatalog((s) => s.load);

  useEffect(() => {
    void load();
    void refreshThreads();
  }, [load]);

  return (
    <div className="app">
      <Sidebar />
      <main className="main">
        {backendError && (
          <div className="banner" role="alert">
            Can't reach the backend ({backendError}). Start it with <code>make backend</code> and reload.
            <button className="btn btn-quiet" onClick={() => void load()}>Retry</button>
          </div>
        )}
        {view === "chat" && <ChatView />}
        {view === "knowledge" && <KnowledgeView />}
        {view === "chains" && <ChainsView />}
      </main>
      <Inspector />
      {open && <div className="scrim" onClick={() => useChat.setState({ sidebarOpen: false, inspectorOpen: false })} aria-hidden />}
    </div>
  );
}
