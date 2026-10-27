# LCEL Chains

LCEL (LangChain Expression Language) lets you compose processing steps with the `|` operator. Every step is a `Runnable` — they share one interface, so they compose freely.

**Source file:** `backend/app/chains/lcel.py`

---

## 1. Prompt | model | parser

The simplest pattern: a prompt template, a chat model, and a string parser piped together.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize the text in {style}."),
    ("human", "{text}"),
])

chain = prompt | llm | StrOutputParser()
result = await chain.ainvoke({"text": "...", "style": "3 bullet points"})
```

The `|` operator calls `.pipe()` under the hood and returns a new `Runnable`. You can call `.invoke()`, `.ainvoke()`, `.stream()`, `.astream()` or `.batch()` on the result.

---

## 2. Structured output

Instead of parsing free text, ask the model to return a Pydantic object:

```python
from pydantic import BaseModel, Field

class Entities(BaseModel):
    people: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)

chain = prompt | llm.with_structured_output(Entities)
result = await chain.ainvoke({"text": "Apple was founded by Steve Jobs in Cupertino."})
# result.people == ["Steve Jobs"]
# result.organizations == ["Apple"]
# result.locations == ["Cupertino"]
```

`.with_structured_output()` uses function calling under the hood when the provider supports it, or falls back to JSON mode. It returns a validated Pydantic instance — no parsing code needed.

---

## 3. RunnableParallel — fan out, collect

Run multiple chains on the same input simultaneously:

```python
from langchain_core.runnables import RunnableParallel

chain = RunnableParallel(
    summary=summary_chain,
    keywords=keyword_chain,
    sentiment=sentiment_chain,
)
result = await chain.ainvoke({"text": "..."})
# result == {"summary": "...", "keywords": "...", "sentiment": {...}}
```

All three branches run concurrently. The output is a dict keyed by name.

---

## 4. RunnableBranch — routing

Route to different chains based on the input:

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: "code" in x["topic"],   code_specialist_chain),
    (lambda x: "math" in x["topic"],   math_specialist_chain),
    general_chain,          # default
)
```

This project uses a classifier LLM call first, then branches on the classified topic:

```python
router = (
    {"topic": classifier_chain, "question": lambda x: x["question"]}
    | branch
)
```

---

## 5. RunnableLambda — arbitrary Python

Wrap any function as a Runnable step:

```python
from langchain_core.runnables import RunnableLambda

format_docs = RunnableLambda(lambda docs: "\n\n".join(d.page_content for d in docs))
```

---

## 6. Retries and fallbacks

```python
# Retry up to 3 times on transient errors (rate limits, timeouts)
robust = llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)

# Fall back to a second model if the first keeps failing
resilient = robust.with_fallbacks([backup_llm])
```

---

## Try it in the UI

Go to the **Chains** tab in the sidebar. Pick a chain, fill in the fields, and click **Run chain**. The output appears below. Read the source in `backend/app/chains/lcel.py` alongside this page — every chain is ~10 lines.
