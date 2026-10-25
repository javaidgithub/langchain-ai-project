import { Brain, Check, ChevronRight, Layers, ListChecks, Pause, X } from "lucide-react";
import { argSummary, stepLabel, toolLabel } from "../lib/labels";
import type { Part, ToolStatus } from "../store/chat";

type TracePart = Exclude<Part, { kind: "text" } | { kind: "reasoning" }>;

function Marker({ status }: { status: ToolStatus | "info" }) {
  return (
    <span className={`marker marker-${status}`} aria-hidden>
      {status === "done" && <Check size={10} strokeWidth={3} />}
      {status === "error" && <X size={10} strokeWidth={3} />}
      {status === "rejected" && <X size={10} strokeWidth={3} />}
      {status === "held" && <Pause size={9} strokeWidth={3} />}
    </span>
  );
}

function Node({ part }: { part: TracePart }) {
  if (part.kind === "step") {
    return (
      <li className="node">
        <Marker status="info" />
        <div className="node-row"><span className="node-title">{stepLabel(part.node)}</span></div>
      </li>
    );
  }

  if (part.kind === "context") {
    return (
      <li className="node">
        <Marker status="info" />
        <details>
          <summary className="node-row">
            <Layers size={14} aria-hidden /> <span className="node-title">Older messages were condensed to save space</span>
            <ChevronRight size={14} className="chev" aria-hidden />
          </summary>
          <p className="node-detail">{part.summary}</p>
        </details>
      </li>
    );
  }

  if (part.kind === "plan") {
    return (
      <li className="node">
        <Marker status="info" />
        <details open>
          <summary className="node-row">
            <ListChecks size={14} aria-hidden /> <span className="node-title">Research plan</span>
            <ChevronRight size={14} className="chev" aria-hidden />
          </summary>
          <ol className="node-detail plan-list">{part.plan.map((s) => <li key={s}>{s}</li>)}</ol>
        </details>
      </li>
    );
  }

  const summary = argSummary(part.args);
  return (
    <li className={`node node-${part.status}`}>
      <Marker status={part.status} />
      <details>
        <summary className="node-row">
          <span className="node-title">{toolLabel(part.name, part.status)}</span>
          {summary && <span className="node-arg">{summary}</span>}
          <ChevronRight size={14} className="chev" aria-hidden />
        </summary>
        <div className="node-detail">
          <pre>{JSON.stringify(part.args, null, 2)}</pre>
          {part.result && <pre className="result">{part.result}</pre>}
        </div>
      </details>
    </li>
  );
}

export function Rail({ parts }: { parts: TracePart[] }) {
  return (
    <ol className="rail" aria-label="Agent activity">
      {parts.map((p, i) => <Node key={i} part={p} />)}
    </ol>
  );
}

export function Reasoning({ text }: { text: string }) {
  return (
    <details className="reasoning">
      <summary><Brain size={14} aria-hidden /> Model reasoning</summary>
      <p>{text}</p>
    </details>
  );
}
