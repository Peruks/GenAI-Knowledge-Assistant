"""
LangChain RAG Chain Module
NEXUS Enterprise Knowledge Assistant

LLM Priority:
1. Gemini 2.5 Flash      (Google — primary)
2. Groq llama-3.1-8b     (Groq — fallback 1)
3. NVIDIA llama-3.1-8b   (NVIDIA NIM — fallback 2)

Features:
- LangChain RetrievalQA chain
- ConversationBufferWindowMemory (last 5 exchanges)
- PromptTemplate for structured prompts
- LLM fallback chain with automatic switching
- Pinecone as vector store via LangChain
"""

import os
from dotenv import load_dotenv

from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY   = os.getenv("NVIDIA_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME       = "enterprise-rag-index"


# ─────────────────────────────────────────────
# 1. LLM Definitions
# ─────────────────────────────────────────────

def get_gemini_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
        max_output_tokens=1024,
        convert_system_message_to_human=True
    )


def get_groq_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=GROQ_API_KEY,
        temperature=0.2,
        max_tokens=1024
    )


def get_nvidia_llm():
    """
    NVIDIA NIM via OpenAI-compatible API.
    Uses langchain_openai.ChatOpenAI with NVIDIA base URL.
    Free at build.nvidia.com
    """
    return ChatOpenAI(
        model="meta/llama-3.1-8b-instruct",
        openai_api_key=NVIDIA_API_KEY,
        openai_api_base="https://integrate.api.nvidia.com/v1",
        temperature=0.2,
        max_tokens=1024
    )


# ─────────────────────────────────────────────
# 2. LLM with Fallback Chain
# ─────────────────────────────────────────────

def get_llm_with_fallback():
    """
    Returns LLM with automatic fallback:
    Gemini → Groq → NVIDIA NIM

    LangChain .with_fallbacks() automatically tries
    the next LLM if the current one raises any exception.
    """
    primary  = get_gemini_llm()
    fallback1 = get_groq_llm()
    fallback2 = get_nvidia_llm()

    return primary.with_fallbacks(
        [fallback1, fallback2],
        exceptions_to_handle=(Exception,)
    )


# ─────────────────────────────────────────────
# 3. Embeddings
# ─────────────────────────────────────────────

def get_embeddings():
    """
    Gemini embeddings via LangChain.
    Same model as main pipeline for consistency.
    """
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GEMINI_API_KEY
    )


# ─────────────────────────────────────────────
# 4. Vector Store Retriever
# ─────────────────────────────────────────────

def get_retriever(top_k: int = 5):
    """
    Pinecone vector store wrapped in LangChain.
    Returns a retriever that fetches top-k relevant chunks.
    """
    embeddings   = get_embeddings()
    vectorstore  = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=PINECONE_API_KEY
    )
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )


# ─────────────────────────────────────────────
# 5. Prompt Template
# ─────────────────────────────────────────────

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an AI assistant for an enterprise knowledge base.

Rules:
- Answer using ONLY the information in the context below
- Do NOT invent or assume any information
- Give complete, well-structured answers with full sentences
- If the answer is not in the context, say exactly:
  "The information is not available in the provided documents"

Context:
{context}

Question:
{question}

Answer:"""
)


# ─────────────────────────────────────────────
# 6. Conversation Memory
# ─────────────────────────────────────────────

# Per-session memory store
_memory_store: dict[str, ConversationBufferWindowMemory] = {}


def get_memory(session_id: str) -> ConversationBufferWindowMemory:
    """
    Returns ConversationBufferWindowMemory for a session.
    Keeps last 5 exchanges to avoid context overflow on free tier.
    Creates new memory if session doesn't exist.
    """
    if session_id not in _memory_store:
        _memory_store[session_id] = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True,
            output_key="result"
        )
    return _memory_store[session_id]


def clear_memory(session_id: str):
    """Clear memory for a specific session."""
    if session_id in _memory_store:
        del _memory_store[session_id]


# ─────────────────────────────────────────────
# 7. RetrievalQA Chain Builder
# ─────────────────────────────────────────────

def build_chain():
    """
    Build the LangChain RetrievalQA chain.
    Components:
    - LLM: Gemini → Groq → NVIDIA fallback
    - Retriever: Pinecone vector store (top-5)
    - Prompt: structured RAG template
    - Chain type: stuff (concatenate all retrieved chunks)
    """
    llm       = get_llm_with_fallback()
    retriever = get_retriever(top_k=5)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": RAG_PROMPT,
            "verbose": False
        }
    )
    return chain


# ─────────────────────────────────────────────
# 8. Main Ask Function
# ─────────────────────────────────────────────

def ask_langchain(question: str, session_id: str) -> dict:
    """
    Run a question through the LangChain RAG pipeline.

    Args:
        question:   User question string
        session_id: Session ID for memory isolation

    Returns:
        dict with answer, sources, session_id, llm_used
    """

    try:
        chain  = build_chain()
        memory = get_memory(session_id)

        # Build history context from memory
        history_messages = memory.load_memory_variables({})
        history_text     = ""

        chat_history = history_messages.get("chat_history", [])
        if chat_history:
            pairs = []
            for msg in chat_history:
                role    = "User" if isinstance(msg, HumanMessage) else "Assistant"
                content = msg.content[:200]
                pairs.append(f"{role}: {content}")
            history_text = "\n".join(pairs)

        # Prepend history to question if exists
        full_question = question
        if history_text:
            full_question = (
                f"Previous conversation:\n{history_text}\n\n"
                f"Current question: {question}"
            )

        # Run chain
        result = chain.invoke({"query": full_question})

        answer   = result.get("result", "No answer returned.")
        src_docs = result.get("source_documents", [])

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

        # Save to memory
        memory.save_context(
            {"input":  question},
            {"result": answer}
        )

        return {
            "answer":     answer,
            "sources":    sources,
            "session_id": session_id,
            "pipeline":   "langchain"
        }

    except Exception as e:
        print(f"LangChain pipeline error: {e}")
        return {
            "answer":     f"LangChain pipeline error: {str(e)}",
            "sources":    [],
            "session_id": session_id,
            "pipeline":   "langchain"
        }