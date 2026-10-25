import { Check, Plus, X } from "lucide-react";
import { useState } from "react";
import type { InterruptValue, ToolCallRequest } from "../api/types";
import { resume } from "../hooks/chatActions";
import { toolLabel } from "../lib/labels";

/** The human-in-the-loop moment: the run is paused until the person decides. */
export function ApprovalGate({ value }: { value: InterruptValue }) {
  return value.type === "tool_approval" ? <ToolGate calls={value.tool_calls} message={value.message} /> : <PlanGate plan={value.plan} message={value.message} />;
}

function ToolGate({ calls, message }: { calls: ToolCallRequest[]; message: string }) {
  const [drafts, setDrafts] = useState<Record<string, string>>(() =>
    Object.fromEntries(calls.map((c) => [c.id, JSON.stringify(c.args, null, 2)])),
  );
  const [feedback, setFeedback] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);

  const edited = calls.filter((c) => drafts[c.id] !== JSON.stringify(c.args, null, 2));

  function approve() {
    try {
      const edits = Object.fromEntries(edited.map((c) => [c.id, JSON.parse(drafts[c.id])]));
      setParseError(null);
      void resume(edited.length ? { action: "edit", edited_args: edits } : { action: "approve" });
    } catch {
      setParseError("The edited arguments are not valid JSON.");
    }
  }

  return (
    <section className="gate" role="alertdialog" aria-labelledby="gate-title">
      <h3 id="gate-title">Waiting for your decision</h3>
      <p className="gate-lead">{message}</p>
      {calls.map((c) => (
        <div className="gate-call" key={c.id}>
          <div className="gate-call-head">
            <strong>{toolLabel(c.name, "running")}</strong>
            <code>{c.name}</code>
            {!c.needs_approval && <span className="tag">runs automatically</span>}
          </div>
          <label className="sr-only" htmlFor={`args-${c.id}`}>Arguments for {c.name}</label>
          <textarea
            id={`args-${c.id}`}
            className="code-input"
            spellCheck={false}
            rows={Math.min(10, drafts[c.id].split("\n").length + 1)}
            value={drafts[c.id]}
            onChange={(e) => setDrafts({ ...drafts, [c.id]: e.target.value })}
          />
        </div>
      ))}
      {parseError && <p className="field-error" role="alert">{parseError}</p>}
      <div className="gate-actions">
        <button className="btn btn-primary" onClick={approve}>
          <Check size={15} aria-hidden /> {edited.length ? "Approve with my edits" : "Approve"}
        </button>
        <input
          className="input grow"
          placeholder="Reason for rejecting (optional)"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          aria-label="Reason for rejecting"
        />
        <button className="btn btn-quiet" onClick={() => void resume({ action: "reject", feedback: feedback.trim() || undefined })}>
          <X size={15} aria-hidden /> Reject
        </button>
      </div>
    </section>
  );
}

function PlanGate({ plan, message }: { plan: string[]; message: string }) {
  const [steps, setSteps] = useState(plan);
  const changed = JSON.stringify(steps) !== JSON.stringify(plan);

  return (
    <section className="gate" role="alertdialog" aria-labelledby="gate-title">
      <h3 id="gate-title">Review the research plan</h3>
      <p className="gate-lead">{message}</p>
      <ol className="plan-edit">
        {steps.map((s, i) => (
          <li key={i}>
            <input
              className="input"
              value={s}
              aria-label={`Step ${i + 1}`}
              onChange={(e) => setSteps(steps.map((x, j) => (j === i ? e.target.value : x)))}
            />
            <button className="icon-btn" aria-label={`Remove step ${i + 1}`} onClick={() => setSteps(steps.filter((_, j) => j !== i))}>
              <X size={15} aria-hidden />
            </button>
          </li>
        ))}
      </ol>
      {steps.length < 5 && (
        <button className="btn btn-quiet" onClick={() => setSteps([...steps, ""])}>
          <Plus size={15} aria-hidden /> Add a step
        </button>
      )}
      <div className="gate-actions">
        <button
          className="btn btn-primary"
          disabled={!steps.some((s) => s.trim())}
          onClick={() => void resume(changed ? { action: "edit", plan: steps } : { action: "approve" })}
        >
          <Check size={15} aria-hidden /> {changed ? "Start with my changes" : "Start research"}
        </button>
        <button className="btn btn-quiet" onClick={() => void resume({ action: "cancel" })}>
          <X size={15} aria-hidden /> Cancel
        </button>
      </div>
    </section>
  );
}
