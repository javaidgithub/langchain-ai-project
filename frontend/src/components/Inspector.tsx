import { ExternalLink, ShieldCheck, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { MemoryItem } from "../api/types";
import { TOOL_CATEGORY_LABELS } from "../lib/labels";
import { useCatalog } from "../store/catalog";
import { useChat } from "../store/chat";
import { useSettings } from "../store/settings";

export function Inspector() {
  const open = useChat((s) => s.inspectorOpen);
  const s = useSettings();
  const { providers, tools } = useCatalog();
  const provider = providers.find((p) => p.id === s.provider);
  const hasLocalKey = Boolean(s.apiKeys[s.provider]);

  const byCategory = tools.reduce<Record<string, typeof tools>>((acc, t) => ((acc[t.category] ??= []).push(t), acc), {});
  const enabled = new Set(s.enabledTools ?? tools.map((t) => t.name));
  const toggle = (name: string) => {
    const next = new Set(enabled);
    next.has(name) ? next.delete(name) : next.add(name);
    s.patch({ enabledTools: next.size === tools.length ? null : [...next] });
  };

  return (
    <aside className={`inspector ${open ? "is-open" : ""}`} aria-label="Settings">
      <div className="inspector-head">
        <h2>Settings</h2>
        <button className="icon-btn only-medium" aria-label="Close settings" onClick={() => useChat.setState({ inspectorOpen: false })}><X size={18} /></button>
      </div>

      <section>
        <h3>Model</h3>
        <label className="field">
          <span>Provider</span>
          <select className="input" value={s.provider}
            onChange={(e) => s.patch({ provider: e.target.value, model: providers.find((p) => p.id === e.target.value)?.models[0] ?? "" })}>
            {providers.map((p) => <option key={p.id} value={p.id}>{p.label}{p.configured ? "" : " (no server key)"}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Model</span>
          <input className="input mono" list="model-options" value={s.model} onChange={(e) => s.patch({ model: e.target.value })} spellCheck={false} />
          <datalist id="model-options">{provider?.models.map((m) => <option key={m} value={m} />)}</datalist>
          <small>Pick a suggestion or type any model id your provider supports.</small>
        </label>
        <label className="field">
          <span>Temperature <b>{s.temperature.toFixed(1)}</b></span>
          <input type="range" min={0} max={1.5} step={0.1} value={s.temperature} onChange={(e) => s.patch({ temperature: Number(e.target.value) })} />
        </label>
        {provider?.needs_key && (
          <label className="field">
            <span>API key {provider.configured && <em className="ok">set on server</em>}</span>
            <input className="input mono" type="password" autoComplete="off" value={s.apiKeys[s.provider] ?? ""}
              placeholder={provider.configured ? "Optional: overrides the server key" : "Paste your key"}
              onChange={(e) => s.setApiKey(s.provider, e.target.value)} />
            <small>
              Stored only in this browser and sent with your requests.{" "}
              {provider.docs_url && <a href={provider.docs_url} target="_blank" rel="noreferrer">Get a key <ExternalLink size={11} aria-hidden /></a>}
            </small>
            {!provider.configured && !hasLocalKey && <small className="warn">No key yet for {provider.label}. Requests will fail until you add one.</small>}
          </label>
        )}
      </section>

      <section>
        <h3>Human in the loop</h3>
        <label className="switch">
          <input type="checkbox" checked={s.requireApproval} onChange={(e) => s.patch({ requireApproval: e.target.checked })} />
          <span><ShieldCheck size={15} aria-hidden /> Ask before risky actions and plans</span>
        </label>
        <small>Sending email, running code and writing files pause for your approval. The Researcher waits for plan approval.</small>
      </section>

      <section>
        <h3>Instructions</h3>
        <label className="field">
          <span className="sr-only">Custom instructions</span>
          <textarea className="input" rows={3} value={s.systemPrompt} placeholder="Optional. For example: answer in Urdu, keep it brief." onChange={(e) => s.patch({ systemPrompt: e.target.value })} />
        </label>
      </section>

      {s.agent === "assistant" && (
        <section>
          <h3>Tools <small>{enabled.size} of {tools.length} on</small></h3>
          {Object.entries(byCategory).map(([cat, list]) => (
            <fieldset key={cat}>
              <legend>{TOOL_CATEGORY_LABELS[cat] ?? cat}</legend>
              {list.map((t) => (
                <label key={t.name} className="tool-row" title={t.description}>
                  <input type="checkbox" checked={enabled.has(t.name)} onChange={() => toggle(t.name)} />
                  <span>{t.name}</span>
                  {t.requires_approval && <span className="tag tag-hold">asks first</span>}
                </label>
              ))}
            </fieldset>
          ))}
        </section>
      )}

      <Memory />
    </aside>
  );
}

function Memory() {
  const [items, setItems] = useState<MemoryItem[]>([]);
  const streaming = useChat((s) => s.streaming);
  useEffect(() => {
    if (!streaming) api.memories().then(setItems).catch(() => setItems([]));
  }, [streaming]);

  return (
    <section>
      <h3>Long-term memory</h3>
      {items.length === 0 ? (
        <small>Nothing saved yet. Tell the assistant to remember something about you.</small>
      ) : (
        <ul className="memories">
          {items.map((m) => (
            <li key={m.id}>
              <span>{m.content}</span>
              <button className="icon-btn" aria-label="Forget this" onClick={() => api.deleteMemory(m.id).then(() => setItems(items.filter((x) => x.id !== m.id)))}><Trash2 size={14} /></button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
