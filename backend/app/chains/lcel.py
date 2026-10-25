"""LCEL (LangChain Expression Language) examples.

Each builder takes a chat model and returns a Runnable. They showcase:
prompt templates, output parsers, structured output, RunnableParallel,
RunnableBranch-style routing, fallbacks/retries and RAG with citations.
"""
from __future__ import annotations

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableBranch, RunnableLambda, RunnableParallel
from pydantic import BaseModel, Field

from app.rag.service import format_docs, get_retriever

parser = StrOutputParser()


# ---------- 1. Prompt | model | parser ----------
def summarize_chain(llm: BaseChatModel) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a precise editor. Summarize the text in {style}."),
        ("human", "{text}"),
    ])
    return (prompt | llm | parser).with_config(run_name="summarize")


def translate_chain(llm: BaseChatModel) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Translate the user's text into {language}. Return only the translation."),
        ("human", "{text}"),
    ])
    return (prompt | llm | parser).with_config(run_name="translate")


# ---------- 2. Structured output ----------
class Entities(BaseModel):
    people: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)


def extraction_chain(llm: BaseChatModel) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract named entities from the text. Only include entities that appear in it."),
        ("human", "{text}"),
    ])
    return (prompt | llm.with_structured_output(Entities) | RunnableLambda(lambda e: e.model_dump())).with_config(
        run_name="extract_entities"
    )


# ---------- 3. RunnableParallel ----------
class Sentiment(BaseModel):
    label: Literal["positive", "neutral", "negative"]
    confidence: float = Field(ge=0, le=1)


def analysis_chain(llm: BaseChatModel) -> Runnable:
    summary = ChatPromptTemplate.from_template("Summarize in one sentence:\n{text}") | llm | parser
    keywords = ChatPromptTemplate.from_template("List 5 comma-separated keywords for:\n{text}") | llm | parser
    sentiment = (
        ChatPromptTemplate.from_template("Classify the sentiment of:\n{text}")
        | llm.with_structured_output(Sentiment)
        | RunnableLambda(lambda s: s.model_dump())
    )
    return RunnableParallel(summary=summary, keywords=keywords, sentiment=sentiment).with_config(run_name="analysis")


# ---------- 4. Routing ----------
def router_chain(llm: BaseChatModel) -> Runnable:
    classify = (
        ChatPromptTemplate.from_template(
            "Classify the request as exactly one word: code, math, or general.\nRequest: {question}"
        )
        | llm
        | parser
        | RunnableLambda(lambda s: s.strip().lower())
    )

    def specialist(system: str) -> Runnable:
        return ChatPromptTemplate.from_messages([("system", system), ("human", "{question}")]) | llm | parser

    branch = RunnableBranch(
        (lambda x: "code" in x["topic"], specialist("You are a senior software engineer. Answer with concise, correct code.")),
        (lambda x: "math" in x["topic"], specialist("You are a math tutor. Show the reasoning step by step.")),
        specialist("You are a helpful assistant. Be concise."),
    )
    return ({"topic": classify, "question": lambda x: x["question"]} | branch).with_config(run_name="router")


# ---------- 5. RAG with citations ----------
def rag_chain(llm: BaseChatModel) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Answer using ONLY the context. Cite sources like [1], [2]. "
         "If the context is insufficient, say you don't know.\n\nContext:\n{context}"),
        ("human", "{question}"),
    ])
    retrieve = RunnableLambda(lambda q: get_retriever().invoke(q))
    return (
        RunnableParallel(docs=retrieve, question=RunnableLambda(lambda q: q))
        | RunnableParallel(
            answer=(RunnableLambda(lambda x: {"context": format_docs(x["docs"]), "question": x["question"]})
                    | prompt | llm | parser),
            docs=RunnableLambda(lambda x: x["docs"]),
        )
    ).with_config(run_name="rag")


# ---------- 6. Reliability ----------
def with_resilience(primary: BaseChatModel, fallback: BaseChatModel | None = None) -> Runnable:
    """Retry transient errors, then fall back to a second model."""
    robust = primary.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
    return robust.with_fallbacks([fallback]) if fallback else robust


CHAINS: dict[str, dict] = {
    "summarize": {"builder": summarize_chain, "description": "Prompt | model | parser. Summarize text in a chosen style.",
                  "fields": {"text": "Text to summarize", "style": "Style, e.g. 3 bullet points"}},
    "translate": {"builder": translate_chain, "description": "Translate text into any language.",
                  "fields": {"text": "Text to translate", "language": "Target language"}},
    "extract": {"builder": extraction_chain, "description": "Structured output with a Pydantic schema.",
                "fields": {"text": "Text to extract entities from"}},
    "analyze": {"builder": analysis_chain, "description": "RunnableParallel: summary, keywords and sentiment in one pass.",
                "fields": {"text": "Text to analyze"}},
    "route": {"builder": router_chain, "description": "Classifies a question, then routes it to a specialist prompt.",
              "fields": {"question": "Your question"}},
}
