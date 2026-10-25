import { ArrowUp, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { send, stop } from "../hooks/chatActions";
import { useChat } from "../store/chat";

export function Composer() {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const streaming = useChat((s) => s.streaming);
  const paused = useChat((s) => s.interrupt !== null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [text]);

  function submit() {
    if (!text.trim() || streaming || paused) return;
    void send(text);
    setText("");
  }

  return (
    <div className="composer">
      {paused && <p className="composer-note" role="status">The agent is paused. Approve or reject the action above to continue.</p>}
      <div className="composer-box">
        <label htmlFor="prompt" className="sr-only">Message</label>
        <textarea
          id="prompt"
          ref={ref}
          rows={1}
          value={text}
          disabled={paused}
          placeholder="Ask anything"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              submit();
            }
          }}
        />
        {streaming ? (
          <button className="send send-stop" onClick={stop} aria-label="Stop generating"><Square size={14} fill="currentColor" /></button>
        ) : (
          <button className="send" onClick={submit} disabled={!text.trim() || paused} aria-label="Send message"><ArrowUp size={18} /></button>
        )}
      </div>
    </div>
  );
}
