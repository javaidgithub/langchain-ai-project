import { AlertTriangle, FileText } from "lucide-react";
import { isTrace } from "../lib/labels";
import type { Msg, Part } from "../store/chat";
import { Markdown } from "./Markdown";
import { Rail, Reasoning } from "./Trace";

type TracePart = Exclude<Part, { kind: "text" } | { kind: "reasoning" }>;

/** Group consecutive trace parts so they share one rail. */
function group(parts: Part[]) {
  const blocks: ({ kind: "rail"; parts: TracePart[] } | Extract<Part, { kind: "text" | "reasoning" }>)[] = [];
  for (const p of parts) {
    if (isTrace(p)) {
      const last = blocks[blocks.length - 1];
      if (last && last.kind === "rail") last.parts.push(p as TracePart);
      else blocks.push({ kind: "rail", parts: [p as TracePart] });
    } else {
      blocks.push(p as Extract<Part, { kind: "text" | "reasoning" }>);
    }
  }
  return blocks;
}

export function MessageView({ msg, live }: { msg: Msg; live: boolean }) {
  if (msg.role === "user") {
    return (
      <div className="msg-user">
        <p>{msg.parts[0].kind === "text" ? msg.parts[0].text : ""}</p>
      </div>
    );
  }

  const blocks = group(msg.parts);
  const empty = blocks.length === 0 && !msg.error;

  return (
    <article className="msg-assistant" aria-busy={live}>
      {empty && live && <p className="thinking" role="status">Thinking</p>}
      {blocks.map((b, i) => {
        if (b.kind === "rail") return <Rail key={i} parts={b.parts} />;
        if (b.kind === "reasoning") return <Reasoning key={i} text={b.text} />;
        return <Markdown key={i}>{b.text}</Markdown>;
      })}
      {msg.sources && msg.sources.length > 0 && (
        <ul className="sources" aria-label="Sources">
          {msg.sources.map((s) => (
            <li key={s.index}>
              <details>
                <summary><FileText size={14} aria-hidden /> [{s.index}] {s.source}{s.page != null ? `, p.${s.page + 1}` : ""}</summary>
                <p>{s.snippet}…</p>
              </details>
            </li>
          ))}
        </ul>
      )}
      {msg.error && (
        <p className="error-note" role="alert"><AlertTriangle size={16} aria-hidden /> {msg.error}</p>
      )}
      {msg.usage && msg.usage.total_tokens > 0 && !live && (
        <p className="usage">{msg.usage.total_tokens.toLocaleString()} tokens across {msg.usage.llm_calls} model call{msg.usage.llm_calls === 1 ? "" : "s"}</p>
      )}
    </article>
  );
}
