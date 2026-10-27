# Concepts Overview

This project is a **complete, working implementation** of the major LangChain and LangGraph patterns. This section explains each concept with diagrams, code excerpts and links to the relevant source files.

## The LangChain stack

```
Your application
       │
       ▼
langchain-core          ← abstractions: chat models, tools, prompts, output parsers
       │
       ├── langchain            ← chains, agents, memory utilities
       ├── langchain-community  ← loaders, vector stores, third-party integrations
       ├── langchain-openai     ← OpenAI models and embeddings
       ├── langchain-anthropic  ← Anthropic Claude
       ├── langchain-google-genai  ← Google Gemini
       └── ...                  ← one package per provider
       │
langgraph               ← stateful, multi-step, branching agent graphs
```

## Where to start

| If you want to understand… | Read |
|---|---|
| How LCEL chains work | [LCEL Chains](lcel-chains.md) |
| How LangGraph agents work | [LangGraph Agents](langgraph-agents.md) |
| How human approval works | [Human-in-the-Loop](human-in-the-loop.md) |
| How documents are indexed and searched | [RAG](rag.md) |
| How long conversations are handled | [Context Management](context-management.md) |
| What tools are available | [Tools](tools.md) |
| How to add a new provider | [Providers](providers.md) |
| How memory works | [Memory](memory.md) |
| How tokens stream to the browser | [Streaming](streaming.md) |
| How token usage is tracked | [Callbacks](callbacks.md) |
