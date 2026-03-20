"""
LangChain RAG Chain Module
NEXUS Enterprise Knowledge Assistant

Uses newer LangChain API (langchain-core, langchain-community)
instead of deprecated langchain.chains

LLM Priority:
1. Gemini 2.5 Flash   (primary)
2. Groq llama-3.1-8b  (fallback 1)
3. NVIDIA NIM         (fallback 2)
"""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY   = os.getenv("NVIDIA_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME       = "enterprise-rag-index"


# ─────────────────────────────────────────────
# LLM Definitions
# ─────────────────────────────────────────────

def get_gemini_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
        convert_system_message_to_human=True
    )


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


# ─────────────────────────────────────────────
# LLM with Fallback Chain
# ─────────────────────────────────────────────

def get_llm_with_fallback():
    primary   = get_gemini_llm()
    fallback1 = get_groq_llm()
    fallback2 = get_nvidia_llm()
    return primary.with_fallbacks(
        [fallback1, fallback2],
        exceptions_to_handle=(Exception,)
    )


# ─────────────────────────────────────────────
# Embeddings
# ─────────────────────────────────────────────

def get_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GEMINI_API_KEY
    )


# ─────────────────────────────────────────────
# Retriever
# ─────────────────────────────────────────────

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
# Prompt Template
# ─────────────────────────────────────────────

RAG_PROMPT_TEMPLATE = """You are an AI assistant for an enterprise knowledge base.

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


# ─────────────────────────────────────────────
# Conversation Memory Store
# ─────────────────────────────────────────────

_memory_store = {}


def get_memory(session_id: str):
    from langchain.memory import ConversationBufferWindowMemory
    if session_id not in _memory_store:
        _memory_store[session_id] = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True,
            output_key="result"
        )
    return _memory_store[session_id]


# ─────────────────────────────────────────────
# Main Ask Function — using LCEL (LangChain Expression Language)
# ─────────────────────────────────────────────

def ask_langchain(question: str, session_id: str) -> dict:
    """
    Run question through LangChain RAG pipeline using LCEL.
    Uses RunnablePassthrough + StrOutputParser instead of
    deprecated RetrievalQA chain.
    """
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough

        llm       = get_llm_with_fallback()
        retriever = get_retriever(top_k=5)
        memory    = get_memory(session_id)

        # Get chat history
        history_vars = memory.load_memory_variables({})
        chat_history = history_vars.get("chat_history", [])

        history_text = ""
        if chat_history:
            from langchain_core.messages import HumanMessage
            pairs = []
            for msg in chat_history:
                role    = "User" if isinstance(msg, HumanMessage) else "Assistant"
                content = msg.content[:200]
                pairs.append(role + ": " + content)
            history_text = "\n".join(pairs)

        full_question = question
        if history_text:
            full_question = (
                "Previous conversation:\n"
                + history_text
                + "\n\nCurrent question: "
                + question
            )

        # Build LCEL chain
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

        # Run chain
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

        # Save to memory
        memory.save_context(
            {"input":  question},
            {"result": answer}
        )

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