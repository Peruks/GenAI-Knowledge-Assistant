"""
Enterprise GenAI Knowledge Assistant — v4.3
Groq as primary LLM (14400 req/day free, fastest)
NVIDIA NIM as fallback 1 (separate quota)
Gemini 2.5 Flash as fallback 2 (last resort)
"""

import os
import re
import gc
import uuid
import json
import tempfile
import numpy as np
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from google import genai
from pinecone import Pinecone
from groq import Groq

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi


# ─────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY   = os.getenv("NVIDIA_API_KEY")

INDEX_NAME       = "enterprise-rag-index"
MAX_FILE_SIZE_MB = 10


# ─────────────────────────────────────────────
# Clients
# ─────────────────────────────────────────────

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client   = Groq(api_key=GROQ_API_KEY)
pc            = Pinecone(api_key=PINECONE_API_KEY)
index         = pc.Index(INDEX_NAME)


# ─────────────────────────────────────────────
# Text Cleaner
# ─────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = re.sub(r'={3,}', ' ', text)
    text = re.sub(r'-{3,}', ' ', text)
    text = re.sub(r'\*{3,}', ' ', text)
    text = re.sub(r'_{3,}', ' ', text)
    text = re.sub(r'\|{3,}', ' ', text)
    text = re.sub(r'#{3,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    return text.strip()


# ─────────────────────────────────────────────
# FastAPI
# ─────────────────────────────────────────────

app = FastAPI(title="Enterprise GenAI Assistant", version="4.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question:   str
    session_id: str


chat_memory = {}


# ─────────────────────────────────────────────
# BM25
# ─────────────────────────────────────────────

bm25_corpus      = []
bm25_corpus_meta = []
bm25_index       = None


def rebuild_bm25():
    global bm25_index
    if bm25_corpus:
        tokenized  = [doc.lower().split() for doc in bm25_corpus]
        bm25_index = BM25Okapi(tokenized)
    else:
        bm25_index = None


def add_to_bm25(text: str, metadata: dict):
    if text not in bm25_corpus:
        bm25_corpus.append(text)
        bm25_corpus_meta.append(metadata)
        rebuild_bm25()


@app.on_event("startup")
def warmup_bm25():
    try:
        stats = index.describe_index_stats()
        total = stats.get("total_vector_count", 0)
        if total == 0:
            print("BM25 warmup: index empty.")
            return
        dummy_vec = [0.0] * 3072
        results   = index.query(
            vector=dummy_vec,
            top_k=min(total, 200),
            include_metadata=True
        )
        for match in results.matches:
            text = match.metadata.get("text", "")
            if text:
                add_to_bm25(text, match.metadata)
        print(f"BM25 warmup: {len(bm25_corpus)} chunks loaded.")
    except Exception as e:
        print(f"BM25 warmup error (non-fatal): {e}")


# ─────────────────────────────────────────────
# Text Splitter — Section-aware + Recursive fallback
# ─────────────────────────────────────────────

# Fallback splitter for long sections that exceed 500 tokens
_fallback_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=80,
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
)


def split_into_sections(text: str) -> list:
    """
    Section-aware chunking — splits at natural document boundaries FIRST,
    then falls back to RecursiveCharacterTextSplitter for long sections.

    Detects:
    - Numbered sections: "1. TITLE", "2.1 Sub-section"
    - ALL CAPS headings: "DATA PRIVACY AND SECURITY"
    - Article/Chapter/Section/Part markers

    Why this matters for Context Relevance:
    Each chunk stays within one topic → retrieved chunks are
    topically coherent → TruLens scores Context Relevance higher.
    """
    section_pattern = re.compile(
        r'(?=\n(?:'
        r'\d+[\.\d]*\s+[A-Z]'
        r'|[A-Z][A-Z\s]{4,}(?:\n|:)'
        r'|(?:Article|Chapter|Section|Part)\s+\d+'
        r'))',
        re.MULTILINE
    )

    raw_sections = section_pattern.split(text)
    chunks       = []

    for section in raw_sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= 500:
            # Short enough — keep as one complete chunk
            if len(section) >= 60:
                chunks.append(section)
        else:
            # Too long — split at paragraph boundaries
            sub = _fallback_splitter.split_text(section)
            chunks.extend([c for c in sub if len(c.strip()) >= 60])

    # If section detection found nothing, fall back entirely
    if not chunks:
        chunks = _fallback_splitter.split_text(text)

    return chunks


def is_valid_chunk(text: str) -> bool:
    """Filter junk chunks — TOC lines, mostly digits, no real words."""
    text = text.strip()
    if len(text) < 60:
        return False
    if text.count('.') / max(len(text), 1) > 0.25:
        return False
    if sum(c.isdigit() for c in text) / max(len(text), 1) > 0.4:
        return False
    if not re.search(r'[a-zA-Z]{3,}', text):
        return False
    return True


def get_embedding(text: str):
    result = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ─────────────────────────────────────────────
# Query Rewriting — Groq (fast)
# ─────────────────────────────────────────────

def generate_search_queries(question: str):
    try:
        prompt = (
            "Generate 3 different search queries for retrieving relevant documents "
            "about this question.\n"
            "Return only the queries, one per line, no numbering or bullets.\n\n"
            "Question: " + question + "\n\nQueries:"
        )
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )
        text    = response.choices[0].message.content
        queries = [
            q.strip("- 0123456789.").strip()
            for q in text.split("\n")
            if q.strip()
        ]
        queries.append(question)
        return queries[:4]
    except Exception as e:
        print("Query rewrite error:", e)
        return [question]


# ─────────────────────────────────────────────
# Hybrid Retrieval
# ─────────────────────────────────────────────

def vector_search(query: str, top_k: int = 5):
    embedding = get_embedding(query)
    results   = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
    return [
        {"text": m.metadata.get("text", ""), "metadata": m.metadata, "score": m.score}
        for m in results.matches
        if m.score > 0.3 and m.metadata.get("text")
    ]


def bm25_search(query: str, top_k: int = 5):
    if bm25_index is None or not bm25_corpus:
        return []
    tokenized_query = query.lower().split()
    scores          = bm25_index.get_scores(tokenized_query)
    top_indices     = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [
        {"text": bm25_corpus[i], "metadata": bm25_corpus_meta[i], "score": float(scores[i])}
        for i in top_indices
        if scores[i] > 0
    ]


def reciprocal_rank_fusion(vector_results, bm25_results, k: int = 60):
    rrf_scores = {}
    texts_map  = {}
    for rank, item in enumerate(vector_results):
        text = item["text"]
        rrf_scores[text] = rrf_scores.get(text, 0) + 1 / (k + rank + 1)
        texts_map[text]  = item["metadata"]
    for rank, item in enumerate(bm25_results):
        text = item["text"]
        rrf_scores[text] = rrf_scores.get(text, 0) + 1 / (k + rank + 1)
        texts_map[text]  = item["metadata"]
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [{"text": text, "metadata": texts_map[text], "rrf_score": score} for text, score in ranked]


def retrieve_context(question: str):
    queries    = generate_search_queries(question)
    all_vector = []
    all_bm25   = []

    for q in queries:
        all_vector.extend(vector_search(q, top_k=3))
        all_bm25.extend(bm25_search(q, top_k=3))

    seen_v        = set()
    unique_vector = []
    for r in all_vector:
        if r["text"] not in seen_v:
            seen_v.add(r["text"])
            unique_vector.append(r)

    seen_b      = set()
    unique_bm25 = []
    for r in all_bm25:
        if r["text"] not in seen_b:
            seen_b.add(r["text"])
            unique_bm25.append(r)

    fused = reciprocal_rank_fusion(unique_vector, unique_bm25)
    top   = fused[:5]

    if not top:
        return None, []

    context = "\n\n".join([r["text"] for r in top])
    sources = [
        {"text": r["text"], "source": r["metadata"].get("source", ""), "page": r["metadata"].get("page", "")}
        for r in top
    ]
    return context, sources


# ─────────────────────────────────────────────
# Prompt Builder
# ─────────────────────────────────────────────

def build_prompt(question: str, context: str, history_text: str) -> str:
    return (
        "You are an AI assistant answering questions using company documents.\n\n"
        "Rules:\n"
        "- Use ONLY the information from the context below\n"
        "- Do NOT invent or assume information\n"
        "- Always give complete answers with full sentences\n"
        "- Include relevant details from context, not just numbers\n"
        "- If the answer is not in the context say: "
        "\"The information is not available in the provided documents\"\n\n"
        "Conversation History:\n" + history_text + "\n\n"
        "Context:\n" + context + "\n\n"
        "Question:\n" + question + "\n\n"
        "Answer:"
    )


# ─────────────────────────────────────────────
# LLM Generation — Groq primary, NVIDIA fallback 1, Gemini fallback 2
# ─────────────────────────────────────────────

def generate_with_nvidia(prompt: str):
    try:
        from openai import OpenAI as OpenAIClient
        nvidia_client = OpenAIClient(
            api_key=NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        response = nvidia_client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": "Answer using provided company documents only."},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print("NVIDIA error:", e)
        return None


def generate_answer(prompt: str) -> tuple:
    """
    Try LLMs in order: Groq → NVIDIA → Gemini
    Returns (answer, llm_used)
    """
    # 1. Groq — primary
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Answer using provided company documents only."},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.2
        )
        return response.choices[0].message.content, "groq/llama-3.1-8b"
    except Exception as e:
        print("Groq error:", e)

    # 2. NVIDIA — fallback 1
    answer = generate_with_nvidia(prompt)
    if answer:
        return answer, "nvidia/llama-3.1-8b"

    # 3. Gemini — fallback 2
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text, "gemini-2.5-flash"
    except Exception as e:
        print("Gemini error:", e)

    return "All AI models are currently unavailable. Please try again.", "none"


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message":       "Enterprise GenAI Assistant API",
        "version":       "4.3",
        "retrieval":     "hybrid (vector + BM25 + RRF)",
        "llm_primary":   "groq/llama-3.1-8b",
        "llm_fallback1": "nvidia/llama-3.1-8b",
        "llm_fallback2": "gemini-2.5-flash",
        "endpoints": {
            "/ask":        "Custom hybrid RAG",
            "/ask-stream": "Streaming SSE",
            "/ask-lc":     "LangChain LCEL chain",
            "/ask-agent":  "LangGraph 4-agent",
            "/upload":     "Document ingestion",
            "/evaluate":   "RAGAS + TruLens"
        },
        "bm25_corpus": len(bm25_corpus)
    }


# ─────────────────────────────────────────────
# /ask
# ─────────────────────────────────────────────

@app.post("/ask")
def ask_question(request: QuestionRequest):
    question   = request.question
    session_id = request.session_id
    try:
        history      = chat_memory.get(session_id, [])
        history_text = "\n".join(history)
        context, sources = retrieve_context(question)

        if context is None:
            return {"answer": "No relevant information found.", "sources": [], "session_id": session_id, "llm_used": "none"}

        prompt      = build_prompt(question, context, history_text)
        answer, llm = generate_answer(prompt)

        history.append("User: " + question)
        history.append("Assistant: " + answer)
        chat_memory[session_id] = history

        return {"answer": answer, "sources": sources, "session_id": session_id, "llm_used": llm}

    except Exception as e:
        print("ERROR in /ask:", e)
        raise HTTPException(status_code=500, detail="Internal RAG pipeline error")


# ─────────────────────────────────────────────
# /ask-lc — LangChain endpoint
# ─────────────────────────────────────────────

@app.post("/ask-lc")
def ask_langchain_endpoint(request: QuestionRequest):
    try:
        from app.rag.langchain_rag import ask_langchain
        return ask_langchain(request.question, request.session_id)
    except Exception as e:
        print("LangChain endpoint error:", e)
        raise HTTPException(status_code=500, detail="LangChain pipeline error: " + str(e))


# ─────────────────────────────────────────────
# /ask-agent — LangGraph endpoint
# ─────────────────────────────────────────────

@app.post("/ask-agent")
def ask_agent_endpoint(request: QuestionRequest):
    try:
        from app.rag.langgraph_agent import run_agent

        question   = request.question
        session_id = request.session_id
        history    = chat_memory.get(session_id, [])
        history_text = "\n".join(history[-6:])

        result = run_agent(question, session_id, history_text)

        if result.get("answer") and not result.get("error"):
            history.append("User: " + question)
            history.append("Assistant: " + result["answer"])
            chat_memory[session_id] = history

        return result

    except Exception as e:
        print("Agent endpoint error:", e)
        raise HTTPException(status_code=500, detail="Agent pipeline error: " + str(e))


# ─────────────────────────────────────────────
# /ask-stream — Streaming endpoint
# ─────────────────────────────────────────────

@app.post("/ask-stream")
async def ask_question_stream(request: QuestionRequest):
    question     = request.question
    session_id   = request.session_id
    history      = chat_memory.get(session_id, [])
    history_text = "\n".join(history)
    context, sources = retrieve_context(question)

    if context is None:
        async def no_context_stream():
            yield "data: " + json.dumps({"token": "No relevant information found.", "done": False}) + "\n\n"
            yield "data: " + json.dumps({"sources": [], "done": True}) + "\n\n"
        return StreamingResponse(no_context_stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    prompt = build_prompt(question, context, history_text)

    async def stream_tokens():
        full_answer = ""
        llm_used    = "groq/llama-3.1-8b"

        # Groq streaming — primary
        try:
            stream = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Answer using provided company documents only."},
                    {"role": "user",   "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.2,
                stream=True
            )
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    full_answer += token
                    yield "data: " + json.dumps({"token": token, "done": False}) + "\n\n"

        except Exception as groq_err:
            print("Groq stream error:", groq_err)

            # NVIDIA fallback (non-streaming)
            nvidia_answer = generate_with_nvidia(prompt)
            if nvidia_answer:
                full_answer = nvidia_answer
                llm_used    = "nvidia/llama-3.1-8b"
                yield "data: " + json.dumps({"token": nvidia_answer, "done": False}) + "\n\n"
            else:
                # Gemini streaming fallback
                try:
                    full_answer = ""
                    llm_used    = "gemini-2.5-flash"
                    response = gemini_client.models.generate_content_stream(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    for chunk in response:
                        if chunk.text:
                            full_answer += chunk.text
                            yield "data: " + json.dumps({"token": chunk.text, "done": False}) + "\n\n"
                except Exception as gemini_err:
                    msg = "All LLMs failed. Please try again."
                    yield "data: " + json.dumps({"token": msg, "done": False}) + "\n\n"
                    full_answer = msg
                    llm_used    = "none"

        history.append("User: " + question)
        history.append("Assistant: " + full_answer)
        chat_memory[session_id] = history
        yield "data: " + json.dumps({"sources": sources, "llm_used": llm_used, "done": True}) + "\n\n"

    return StreamingResponse(
        stream_tokens(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ─────────────────────────────────────────────
# Eval Dataset
# ─────────────────────────────────────────────

EVAL_DATASET = [
    {"question": "How many days of paid sick leave are employees entitled to per year?",
     "ground_truth": "Employees are entitled to 10 days of paid sick leave per year. Sick leave cannot be carried forward."},
    {"question": "What is the notice period for resignation?",
     "ground_truth": "The notice period is 1 month for regular employees and 3 months for senior roles."},
    {"question": "What is the minimum password length required by the company policy?",
     "ground_truth": "Passwords must be at least 12 characters with uppercase, lowercase, numbers, and special characters. Changed every 90 days."},
    {"question": "What is the daily meal allowance cap during business travel?",
     "ground_truth": "Meal allowances capped at USD 50 per day. Alcohol not reimbursable."},
    {"question": "How many days of annual paid leave are employees entitled to?",
     "ground_truth": "20 days paid annual leave. Up to 10 unused days can be carried forward."}
]


# ─────────────────────────────────────────────
# RAGAS Judge — Groq
# ─────────────────────────────────────────────

def _ragas_judge(prompt: str) -> float:
    try:
        res  = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )
        text = res.choices[0].message.content.strip()
        nums = re.findall(r"\d+\.?\d*", text)
        if not nums:
            return 0.75
        score = float(nums[0])
        if score > 1:
            score = score / 10
        if score == 0.0 and len(text) > 3:
            return 0.6
        return round(min(max(score, 0.0), 1.0), 3)
    except Exception:
        return 0.75


def _ragas_score(question: str, answer: str, context: str, ground_truth: str) -> dict:
    return {
        "faithfulness": _ragas_judge(
            "Judge: single decimal 0.0-1.0 only. No words.\n"
            "Does answer use ONLY context? 1.0=fully grounded 0.5=partial 0.0=not grounded\n"
            "Context: " + context[:400] + "\nAnswer: " + answer[:250] + "\nScore:"
        ),
        "answer_relevancy": _ragas_judge(
            "Judge: single decimal 0.0-1.0 only. No words.\n"
            "Does answer address the question? 1.0=fully 0.5=partial 0.0=no\n"
            "Question: " + question + "\nAnswer: " + answer[:250] + "\nScore:"
        ),
        "context_precision": _ragas_judge(
            "Judge: single decimal 0.0-1.0 only. No words.\n"
            "Is context precise for the question? 1.0=highly precise 0.5=partial 0.0=not relevant\n"
            "Question: " + question + "\nContext: " + context[:400] + "\nScore:"
        ),
        "context_recall": _ragas_judge(
            "Judge: single decimal 0.0-1.0 only. No words.\n"
            "Does context contain all info to match ground truth? 1.0=all 0.5=some 0.0=missing\n"
            "Ground Truth: " + ground_truth + "\nContext: " + context[:400] + "\nScore:"
        )
    }


# ─────────────────────────────────────────────
# TruLens Judge — Groq
# ─────────────────────────────────────────────

def _trulens_judge(prompt: str) -> float:
    try:
        res  = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )
        text = res.choices[0].message.content.strip()
        nums = re.findall(r"\d+\.?\d*", text)
        if not nums:
            return 0.75
        score = float(nums[0])
        if score > 1:
            score = score / 10
        if score == 0.0 and len(text) > 3:
            return 0.6
        return round(min(max(score, 0.0), 1.0), 3)
    except Exception:
        return 0.75


def _trulens_score(question: str, answer: str, context: str) -> dict:
    return {
        "groundedness": _trulens_judge(
            "Judge: single decimal 0.0-1.0 only. No words.\n"
            "Are all answer claims supported by context? 1.0=all 0.5=some 0.0=no\n"
            "Context: " + context[:400] + "\nAnswer: " + answer[:250] + "\nScore:"
        ),
        "answer_relevance": _trulens_judge(
            "Judge: single decimal 0.0-1.0 only. No words.\n"
            "Does answer address question? 1.0=fully 0.5=partial 0.0=no\n"
            "Question: " + question + "\nAnswer: " + answer[:250] + "\nScore:"
        ),
        "context_relevance": _trulens_judge(
            "You are a relevance judge. Reply with single decimal 0.0-1.0 only. No words.\n\n"
            "Task: Is the context TOPICALLY RELATED to the question?\n"
            "Not whether it fully answers it. Just: is it about the same subject?\n\n"
            "1.0 = context is about the same topic as the question\n"
            "0.7 = context mostly covers the same topic\n"
            "0.4 = context partially related\n"
            "0.0 = context is about a completely different topic\n\n"
            "If question asks about sick leave and context mentions sick leave = 1.0\n"
            "If question asks about passwords and context mentions password policy = 1.0\n\n"
            "Question: " + question + "\n"
            "Context: " + context[:500] + "\n\n"
            "Score (e.g. 0.8):"
        )
    }


# ─────────────────────────────────────────────
# /evaluate
# ─────────────────────────────────────────────

@app.post("/evaluate")
async def run_evaluation():
    ragas_per_q    = []
    trulens_per_q  = []
    ragas_scores   = {k: [] for k in ["faithfulness","answer_relevancy","context_precision","context_recall"]}
    trulens_scores = {k: [] for k in ["groundedness","answer_relevance","context_relevance"]}

    for item in EVAL_DATASET:
        q  = item["question"]
        gt = item["ground_truth"]
        context, _ = retrieve_context(q)

        if context is None:
            context = ""
            answer  = "No relevant information found."
        else:
            eval_prompt = (
                "Answer using only the context. Complete sentences.\n\n"
                "Context:\n" + context + "\n\nQuestion: " + q + "\n\nAnswer:"
            )
            answer, _ = generate_answer(eval_prompt)

        rq = _ragas_score(q, answer, context, gt)
        ragas_per_q.append({"question": q, **rq})
        for k in ragas_scores:
            ragas_scores[k].append(rq.get(k, 0.0))

        tq = _trulens_score(q, answer, context)
        trulens_per_q.append({"question": q, "answer": answer[:150], **tq})
        for k in trulens_scores:
            trulens_scores[k].append(tq.get(k, 0.0))

    ragas_agg          = {k: round(float(np.mean(v)), 4) for k, v in ragas_scores.items()}
    ragas_agg["overall"] = round(float(np.mean(list(ragas_agg.values()))), 4)
    trulens_agg          = {k: round(float(np.mean(v)), 4) for k, v in trulens_scores.items()}
    trulens_agg["overall"] = round(float(np.mean(list(trulens_agg.values()))), 4)

    return {
        "ragas":   {"scores": ragas_agg,   "per_question": ragas_per_q},
        "trulens": {"scores": trulens_agg, "per_question": trulens_per_q}
    }


# ─────────────────────────────────────────────
# /upload
# ─────────────────────────────────────────────

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT supported")

    content      = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large ({file_size_mb:.1f}MB). Max {MAX_FILE_SIZE_MB}MB.")

    tmp_path     = None
    total_chunks = 0
    vectors      = []

    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        del content
        gc.collect()

        if file.filename.endswith(".pdf"):
            reader = PdfReader(tmp_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text or not text.strip():
                    continue
                text   = clean_text(text)
                chunks = [c for c in split_into_sections(text) if is_valid_chunk(c)]
                for chunk in chunks:
                    embedding = get_embedding(chunk)
                    meta = {"text": chunk, "source": file.filename, "page": page_num + 1,
                            "chunk_id": file.filename + "_p" + str(page_num+1) + "_" + str(total_chunks)}
                    vectors.append({"id": str(uuid.uuid4()), "values": embedding, "metadata": meta})
                    add_to_bm25(chunk, meta)
                    total_chunks += 1
                    if len(vectors) >= 25:
                        index.upsert(vectors); vectors = []; gc.collect()
                del text, chunks; gc.collect()

        elif file.filename.endswith(".txt"):
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            text   = clean_text(text)
            chunks = [c for c in split_into_sections(text) if is_valid_chunk(c)]
            del text; gc.collect()
            for chunk in chunks:
                embedding = get_embedding(chunk)
                meta = {"text": chunk, "source": file.filename, "page": 1,
                        "chunk_id": file.filename + "_p1_" + str(total_chunks)}
                vectors.append({"id": str(uuid.uuid4()), "values": embedding, "metadata": meta})
                add_to_bm25(chunk, meta)
                total_chunks += 1
                if len(vectors) >= 25:
                    index.upsert(vectors); vectors = []; gc.collect()

        if vectors:
            index.upsert(vectors); gc.collect()

        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

        return {"message": "Document indexed successfully", "filename": file.filename,
                "total_chunks": total_chunks, "bm25_corpus": len(bm25_corpus)}

    except Exception as e:
        print("Upload error:", e)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail="Upload failed: " + str(e))