# Your First Conversation

A guided walkthrough of each feature.

## Safe tool use

Try: *"What is sqrt(1764) plus 10% of 500?"*

- The agent uses the `calculator` tool.
- A **trace rail** appears beside the reply showing the tool call and result.
- Expand any node to inspect the exact arguments and output.

## Human-in-the-loop approval

Try: *"Email ceo@example.com a one-line meeting reminder."*

1. A **saffron approval gate** appears — the run is paused.
2. You see the tool name and its arguments in an editable JSON box.
3. **Approve** to run as-is, **edit** the JSON then approve to change arguments, or **reject** with feedback.
4. After approving, the trace rail updates and the reply completes.

!!! tip
    Disable approvals for a session with the **Human in the loop** toggle in Settings.

## Documents agent

1. Go to **Documents** in the sidebar and upload a PDF or text file.
2. Switch the agent to **Documents** in Chat.
3. Ask a question — the agent retrieves chunks, checks relevance, and answers with **[1] [2] citations** you can expand.

## Researcher agent

Try: *"Research open-source LLMs in 2025."*

1. A plan appears — 2–4 research steps.
2. An **approval gate** lets you edit steps or cancel.
3. Steps execute in **parallel**.
4. The writer produces a structured Markdown report with sources.

## Settings panel

- **Provider / Model** — switch at any time; type any model id your provider supports.
- **API key** — paste a per-session key stored only in your browser.
- **Instructions** — a custom system prompt for this session.
- **Tools** — enable or disable individual tools.
- **Long-term memory** — view and delete saved facts.
