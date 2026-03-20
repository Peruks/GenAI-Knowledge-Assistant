"""
LangChain RAG Chain Module
NEXUS Enterprise Knowledge Assistant

Uses LCEL (LangChain Expression Language) — modern API.
No deprecated imports (no langchain.chains, no langchain.memory).

LLM Priority:
1. Groq llama-3.1-8b   (primary  — fast, 14400 req/day free)
2. NVIDIA NIM          (fallback 1 — separate quota)
3. Gemini 2.5 Flash    (fallback 2 — last resort)
"""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY   = os.getenv("NVIDIA_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME       = "enterprise-rag-index"

# Per-session chat history store (replaces langchain.memory)
_history_store: dict = {}

RAG_PROMPT_TEMPLATE = """You are an AI assistant for an enterprise knowledge base.

Rules:
- Answer using ONLY the information in the context below
- Do NOT invent or assume any information
- Give complete, well-structured answers with full sentences
- If the answer is not in the context say exactly:
  "The information is not available in the provided documents"

Context:
{context}

Question:
{question}

Answer:"""


# ─────────────────────────────────────────────
# LLM Definitions — Groq primary
# ─────────────────────────────────────────────

def get_groq_llm():
    from langchain_groq import ChatGroq
    return ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=GROQ_API_KEY,
        temperature=0.2,
        max_tokens=1024
    )


def get_nvidia_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model="meta/llama-3.1-8b-instruct",
        openai_api_key=NVIDIA_API_KEY,
        openai_api_base="https://integrate.api.nvidia.com/v1",
        temperature=0.2,
        max_tokens=1024
    )


def get_gemini_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
        convert_system_message_to_human=True
    )


def get_llm_with_fallback():
    """Groq → NVIDIA → Gemini fallback chain."""
    primary   = get_groq_llm()
    fallback1 = get_nvidia_llm()
    fallback2 = get_gemini_llm()
    return primary.with_fallbacks(
        [fallback1, fallback2],
        exceptions_to_handle=(Exception,)
    )


# ─────────────────────────────────────────────
# Embeddings + Retriever
# ─────────────────────────────────────────────

def get_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GEMINI_API_KEY
    )


def get_retriever(top_k: int = 5):
    from langchain_pinecone import PineconeVectorStore
    embeddings  = get_embeddings()
    vectorstore = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=PINECONE_API_KEY
    )
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )


# ─────────────────────────────────────────────
# Simple in-memory chat history (replaces langchain.memory)
# ─────────────────────────────────────────────

def get_history(session_id: str) -> list:
    return _history_store.get(session_id, [])


def save_history(session_id: str, question: str, answer: str):
    history = _history_store.get(session_id, [])
    history.append({"role": "user",      "content": question})
    history.append({"role": "assistant", "content": answer})
    # Keep last 10 messages (5 exchanges)
    _history_store[session_id] = history[-10:]


def format_history(session_id: str) -> str:
    history = get_history(session_id)
    if not history:
        return ""
    lines = []
    for msg in history:
        role    = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"][:200]
        lines.append(role + ": " + content)
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main Ask Function — LCEL chain
# ─────────────────────────────────────────────

def ask_langchain(question: str, session_id: str) -> dict:
    """
    LangChain LCEL RAG pipeline.
    Groq → NVIDIA → Gemini fallback.
    """
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough

        llm       = get_llm_with_fallback()
        retriever = get_retriever(top_k=5)

        # Build question with history context
        history_text  = format_history(session_id)
        full_question = question
        if history_text:
            full_question = (
                "Previous conversation:\n"
                + history_text
                + "\n\nCurrent question: "
                + question
            )

        # LCEL chain
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {
                "context":  retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        answer   = chain.invoke(full_question)
        src_docs = retriever.invoke(full_question)

        # Format sources
        sources = []
        seen    = set()
        for doc in src_docs:
            text = doc.page_content
            if text not in seen:
                seen.add(text)
                sources.append({
                    "text":   text,
                    "source": doc.metadata.get("source", ""),
                    "page":   doc.metadata.get("page", "")
                })

        # Save to history
        save_history(session_id, question, answer)

        return {
            "answer":     answer,
            "sources":    sources,
            "session_id": session_id,
            "pipeline":   "langchain-lcel"
        }

    except Exception as e:
        print(f"LangChain pipeline error: {e}")
        return {
            "answer":     f"LangChain pipeline error: {str(e)}",
            "sources":    [],
            "session_id": session_id,
            "pipeline":   "langchain-lcel"
        }