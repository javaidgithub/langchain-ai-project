import json
from datetime import UTC, datetime

from langchain_core.tools import tool

from app.core.config import get_settings


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email. Requires human approval.

    This is a *simulated* integration: messages are appended to `data/workspace/outbox.jsonl`.
    Replace the body with SMTP / SendGrid / Gmail API calls for real delivery."""
    outbox = get_settings().workspace_dir / "outbox.jsonl"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    record = {"sent_at": datetime.now(UTC).isoformat(), "to": to, "subject": subject, "body": body}
    with outbox.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    return f"Email to {to} queued with subject '{subject}'."
