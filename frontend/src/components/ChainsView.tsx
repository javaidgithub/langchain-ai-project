import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ChainInfo } from "../api/types";
import { currentModel } from "../lib/modelBody";

const DEFAULTS: Record<string, Record<string, string>> = {
  summarize: { style: "3 short bullet points" },
  translate: { language: "Urdu" },
};

export function ChainsView() {
  const [chains, setChains] = useState<ChainInfo[]>([]);
  const [active, setActive] = useState<string>("");
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [output, setOutput] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.chains().then((c) => { setChains(c); if (c[0]) pick(c[0].id); }).catch((e: Error) => setError(e.message));
  }, []);

  function pick(id: string) {
    setActive(id);
    setInputs(DEFAULTS[id] ?? {});
    setOutput(null);
    setError(null);
  }

  async function run() {
    setRunning(true);
    setError(null);
    try {
      setOutput((await api.runChain(active, inputs, currentModel())).output);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  const chain = chains.find((c) => c.id === active);

  return (
    <div className="page">
      <h1>Chains</h1>
      <p className="lead">Small LCEL pipelines that run on the model selected in Settings. Read their source in <code>backend/app/chains/lcel.py</code>.</p>

      <div className="tabs" role="tablist">
        {chains.map((c) => (
          <button key={c.id} role="tab" aria-selected={c.id === active} className={c.id === active ? "is-active" : ""} onClick={() => pick(c.id)}>{c.id}</button>
        ))}
      </div>

      {chain && (
        <div className="chain-form">
          <p className="muted">{chain.description}</p>
          {Object.entries(chain.fields).map(([name, label]) => (
            <label className="field" key={name}>
              <span>{label}</span>
              {name === "text" || name === "question" ? (
                <textarea className="input" rows={5} value={inputs[name] ?? ""} onChange={(e) => setInputs({ ...inputs, [name]: e.target.value })} />
              ) : (
                <input className="input" value={inputs[name] ?? ""} onChange={(e) => setInputs({ ...inputs, [name]: e.target.value })} />
              )}
            </label>
          ))}
          <button className="btn btn-primary" disabled={running} onClick={() => void run()}>{running ? "Running…" : "Run chain"}</button>
        </div>
      )}

      {error && <p className="error-note" role="alert">{error}</p>}
      {output != null && (
        <pre className="output">{typeof output === "string" ? output : JSON.stringify(output, null, 2)}</pre>
      )}
    </div>
  );
}
