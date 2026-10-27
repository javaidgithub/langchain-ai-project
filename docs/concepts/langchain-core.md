# LangChain Core

`langchain-core` defines the base abstractions that everything else builds on. You rarely import it directly, but understanding it makes the rest click.

## The Runnable interface

Every LangChain component — a prompt, a model, an output parser, a retriever, a chain — implements `Runnable`. This means they all share the same interface:

```python
component.invoke(input)           # synchronous, returns output
await component.ainvoke(input)    # async
component.stream(input)           # synchronous iterator of chunks
await component.astream(input)    # async iterator
component.batch([input1, input2]) # parallel batch
```

Because they share one interface, you can pipe them with `|`:

```python
chain = prompt | model | parser
result = await chain.ainvoke({"text": "Hello"})
```

This is LCEL — the LangChain Expression Language. See [LCEL Chains](lcel-chains.md).

## Messages

Chat models exchange `BaseMessage` objects, not raw strings:

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is 2+2?"),
    AIMessage(content="4"),
]
```

`AIMessage` can carry `tool_calls` — structured requests for tools — and `ToolMessage` carries the results back. This is how tool use works in all three agents.

## Prompt templates

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}. Answer in {language}."),
    ("human", "{question}"),
])
# Filled at runtime:
filled = prompt.invoke({"role": "chef", "language": "French", "question": "How do I make roux?"})
```

## Output parsers

```python
from langchain_core.output_parsers import StrOutputParser
parser = StrOutputParser()
# Extracts the text content from an AIMessage
chain = prompt | model | parser
```

For structured data, use `.with_structured_output(MyPydanticModel)` — see [LCEL Chains](lcel-chains.md#2-structured-output).

## Source files

| File | What it shows |
|---|---|
| `backend/app/agents/prompts.py` | System prompts as string templates |
| `backend/app/chains/lcel.py` | Prompt templates, parsers and structured output |
| `backend/app/agents/context.py` | Message manipulation with `RemoveMessage`, `trim_messages` |
