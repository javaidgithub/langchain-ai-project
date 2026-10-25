import { FileText, Trash2, Upload } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { KnowledgeDoc, Source } from "../api/types";
import { currentModel } from "../lib/modelBody";
import { Markdown } from "./Markdown";

export function KnowledgeView() {
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<{ answer: string; sources: Source[] } | null>(null);
  const [asking, setAsking] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(() => api.documents().then(setDocs).catch((e: Error) => setError(e.message)), []);
  useEffect(() => { void refresh(); }, [refresh]);

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    setError(null);
    try {
      for (const f of Array.from(files)) await api.uploadDocument(f);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function ask() {
    if (!question.trim()) return;
    setAsking(true);
    setError(null);
    try {
      setResult(await api.ragQuery(question, currentModel()));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="page">
      <h1>Documents</h1>
      <p className="lead">Upload files to build a knowledge base. The Documents agent and the search_knowledge_base tool both read from it.</p>

      <div className="dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); void upload(e.dataTransfer.files); }}>
        <Upload size={20} aria-hidden />
        <p>{busy ? "Reading and indexing…" : "Drop PDF, text, Markdown, CSV or JSON files here"}</p>
        <button className="btn btn-quiet" disabled={busy} onClick={() => fileRef.current?.click()}>Choose files</button>
        <input ref={fileRef} type="file" multiple hidden accept=".pdf,.txt,.md,.markdown,.csv,.json" onChange={(e) => void upload(e.target.files)} />
      </div>

      {error && <p className="error-note" role="alert">{error}</p>}

      <h2>Indexed files</h2>
      {docs.length === 0 ? <p className="muted">No documents yet.</p> : (
        <ul className="doc-list">
          {docs.map((d) => (
            <li key={d.name}>
              <FileText size={16} aria-hidden /> <span>{d.name}</span> <span className="muted">{d.chunks} chunks</span>
              <button className="icon-btn" aria-label={`Remove ${d.name}`} onClick={() => api.deleteDocument(d.name).then(refresh)}><Trash2 size={15} /></button>
            </li>
          ))}
        </ul>
      )}

      <h2>Quick question</h2>
      <p className="muted">A single retrieval chain with citations. For multi-turn answers with query rewriting, use the Documents agent in Chat.</p>
      <div className="row">
        <input className="input grow" value={question} placeholder="Ask about your documents" aria-label="Question"
          onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void ask()} />
        <button className="btn btn-primary" disabled={asking || !question.trim()} onClick={() => void ask()}>{asking ? "Searching…" : "Ask"}</button>
      </div>
      {result && (
        <div className="answer">
          <Markdown>{result.answer}</Markdown>
          <ul className="sources">
            {result.sources.map((s) => (
              <li key={s.index}><details><summary><FileText size={14} aria-hidden /> [{s.index}] {s.source}{s.page != null ? `, p.${s.page + 1}` : ""}</summary><p>{s.snippet}…</p></details></li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
