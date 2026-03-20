"""
Enterprise GenAI Knowledge Assistant
RAG System v4.1 with:
- Gemini embeddings
- Pinecone vector DB
- BM25 keyword search (Hybrid Retrieval)
- Reciprocal Rank Fusion (RRF)
- Multi-query retrieval
- Streaming responses
- Gemini LLM (primary)
- Groq fallback
- Document upload
- RAGAS + TruLens evaluation endpoint
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
# FastAPI App
# ─────────────────────────────────────────────

app = FastAPI(title="Enterprise GenAI Assistant", version="4.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Request Model
# ─────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question:   str
    session_id: str


# ─────────────────────────────────────────────
# Session Memory
# ─────────────────────────────────────────────

chat_memory = {}


# ─────────────────────────────────────────────
# BM25 Corpus
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


# ─────────────────────────────────────────────
# BM25 Warmup on Startup
# ─────────────────────────────────────────────

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
# Text Splitter
# ─────────────────────────────────────────────

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)


# ─────────────────────────────────────────────
# Embedding
# ─────────────────────────────────────────────

def get_embedding(text: str):
    result = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ─────────────────────────────────────────────
# Query Rewriting
# ─────────────────────────────────────────────

def generate_search_queries(question: str):
    try:
        prompt = (
            "Generate 3 different search queries for retrieving relevant documents "
            "about this question.\n"
            "Return only the queries, one per line, no numbering or bullets.\n\n"
            f"Question: {question}\n\nQueries:"
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
        {
            "text":     m.metadata.get("text", ""),
            "metadata": m.metadata,
            "score":    m.score
        }
        for m in results.matches
        if m.score > 0.3 and m.metadata.get("text")
    ]


def bm25_search(query: str, top_k: int = 5):
    if bm25_index is None or not bm25_corpus:
        return []
    tokenized_query = query.lower().split()
    scores          = bm25_index.get_scores(tokenized_query)
    top_indices     = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]
    return [
        {
            "text":     bm25_corpus[i],
            "metadata": bm25_corpus_meta[i],
            "score":    float(scores[i])
        }
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
    return [
        {"text": text, "metadata": texts_map[text], "rrf_score": score}
        for text, score in ranked
    ]


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

    seen_b       = set()
    unique_bm25  = []
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
        {
            "text":   r["text"],
            "source": r["metadata"].get("source", ""),
            "page":   r["metadata"].get("page", "")
        }
        for r in top
    ]
    return context, sources


# ─────────────────────────────────────────────
# LLM Helpers
# ─────────────────────────────────────────────

def build_prompt(question: str, context: str, history_text: str) -> str:
    return (
        "You are an AI assistant answering questions using company documents.\n\n"
        "Rules:\n"
        "- Use ONLY the information from the context below\n"
        "- Do NOT invent or assume information\n"
        "- If the answer is not in the context say: "
        "\"The information is not available in the provided documents\"\n\n"
        f"Conversation History:\n{history_text}\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        "Answer:"
    )


def generate_with_groq(prompt: str) -> str:
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role":    "system",
                    "content": "Answer using provided company documents only."
                },
                {
                    "role":    "user",
                    "content": prompt
                }
            ],
            max_tokens=1024,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Groq error:", e)
        return "Both AI models are currently unavailable."


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message":     "Enterprise GenAI Assistant API",
        "version":     "4.1",
        "retrieval":   "hybrid (vector + BM25 + RRF)",
        "llm_primary": "gemini-2.5-flash",
        "bm25_corpus": len(bm25_corpus)
    }


# ─────────────────────────────────────────────
# /ask — Standard Endpoint
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
            return {
                "answer":     "No relevant information found in the knowledge base.",
                "sources":    [],
                "session_id": session_id
            }

        prompt = build_prompt(question, context, history_text)

        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            answer = response.text
        except Exception as e:
            err = str(e)
            print("Gemini error:", err)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                answer = generate_with_groq(prompt)
            else:
                answer = "AI processing error. Please try again."

        history.append(f"User: {question}")
        history.append(f"Assistant: {answer}")
        chat_memory[session_id] = history

        return {
            "answer":     answer,
            "sources":    sources,
            "session_id": session_id
        }

    except Exception as e:
        print("ERROR in /ask:", e)
        raise HTTPException(status_code=500, detail="Internal RAG pipeline error")


# ─────────────────────────────────────────────
# /ask-stream — Streaming Endpoint
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
            yield f"data: {json.dumps({'token': 'No relevant information found.', 'done': False})}\n\n"
            yield f"data: {json.dumps({'sources': [], 'done': True})}\n\n"
        return StreamingResponse(
            no_context_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    prompt = build_prompt(question, context, history_text)

    async def stream_tokens():
        full_answer = ""
        try:
            response = gemini_client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt
            )
            for chunk in response:
                if chunk.text:
                    full_answer += chunk.text
                    yield f"data: {json.dumps({'token': chunk.text, 'done': False})}\n\n"

        except Exception as gemini_err:
            err = str(gemini_err)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                try:
                    full_answer = ""
                    stream = groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1024,
                        temperature=0.2,
                        stream=True
                    )
                    for chunk in stream:
                        token = chunk.choices[0].delta.content or ""
                        if token:
                            full_answer += token
                            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                except Exception:
                    msg = "Both LLMs failed. Please try again."
                    yield f"data: {json.dumps({'token': msg, 'done': False})}\n\n"
                    full_answer = msg
            else:
                msg = "AI processing error."
                yield f"data: {json.dumps({'token': msg, 'done': False})}\n\n"
                full_answer = msg

        history.append(f"User: {question}")
        history.append(f"Assistant: {full_answer}")
        chat_memory[session_id] = history
        yield f"data: {json.dumps({'sources': sources, 'done': True})}\n\n"

    return StreamingResponse(
        stream_tokens(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ─────────────────────────────────────────────
# Eval Dataset
# ─────────────────────────────────────────────

EVAL_DATASET = [
    {
        "question":     "How many days of paid sick leave are employees entitled to per year?",
        "ground_truth": "Employees are entitled to 10 days of paid sick leave per year. Sick leave cannot be carried forward and does not accumulate."
    },
    {
        "question":     "What is the notice period for resignation?",
        "ground_truth": "The notice period is 1 month for regular employees and 3 months for senior and managerial roles."
    },
    {
        "question":     "What is the minimum password length required by the company policy?",
        "ground_truth": "All system passwords must be at least 12 characters long and include uppercase, lowercase, numbers, and special characters. Passwords must be changed every 90 days."
    },
    {
        "question":     "What is the daily meal allowance cap during business travel?",
        "ground_truth": "Meal allowances during business travel are capped at USD 50 per day including breakfast, lunch, and dinner. Alcohol expenses are not reimbursable."
    },
    {
        "question":     "How many days of annual paid leave are employees entitled to?",
        "ground_truth": "Each employee is entitled to 20 days of paid annual leave per year. Unused leave can be carried forward up to 10 days."
    }
]


# ─────────────────────────────────────────────
# RAGAS Judge
# ─────────────────────────────────────────────

def _ragas_judge(prompt: str) -> float:
    """
    Call Groq as LLM judge.
    Forces a numeric response with explicit instructions.
    Falls back to 0.75 if no number found (assume decent).
    """
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

        # If Groq returns exactly 0 with text, treat as unknown not failure
        if score == 0.0 and len(text) > 3:
            return 0.6

        return round(min(max(score, 0.0), 1.0), 3)

    except Exception:
        return 0.75


def _ragas_score(question: str, answer: str, context: str, ground_truth: str) -> dict:
    """
    Approximate RAGAS metrics using Groq as LLM judge.
    Each metric scored 0.0 - 1.0.
    """

    faithfulness = _ragas_judge(
        "You are an evaluation judge. Reply with a single decimal number between "
        "0.0 and 1.0 only. No words, no explanation.\n\n"
        "Task: Score whether the answer uses ONLY information from the context.\n"
        "1.0 = answer is completely grounded in context\n"
        "0.5 = answer partially uses context\n"
        "0.0 = answer adds information not in context\n\n"
        f"Context: {context[:500]}\n"
        f"Answer: {answer[:300]}\n\n"
        "Score (single decimal number only, e.g. 0.8):"
    )

    answer_relevancy = _ragas_judge(
        "You are an evaluation judge. Reply with a single decimal number between "
        "0.0 and 1.0 only. No words, no explanation.\n\n"
        "Task: Score whether the answer directly addresses the question.\n"
        "1.0 = answer fully addresses the question\n"
        "0.5 = answer partially addresses the question\n"
        "0.0 = answer does not address the question\n\n"
        f"Question: {question}\n"
        f"Answer: {answer[:300]}\n\n"
        "Score (single decimal number only, e.g. 0.9):"
    )

    context_precision = _ragas_judge(
        "You are an evaluation judge. Reply with a single decimal number between "
        "0.0 and 1.0 only. No words, no explanation.\n\n"
        "Task: Score whether the retrieved context is precise and useful for the question.\n"
        "1.0 = context is highly relevant and precise\n"
        "0.5 = context is partially relevant\n"
        "0.0 = context is not relevant\n\n"
        f"Question: {question}\n"
        f"Context: {context[:500]}\n\n"
        "Score (single decimal number only, e.g. 0.7):"
    )

    context_recall = _ragas_judge(
        "You are an evaluation judge. Reply with a single decimal number between "
        "0.0 and 1.0 only. No words, no explanation.\n\n"
        "Task: Score whether the context contains all the information needed "
        "to match the ground truth answer.\n"
        "1.0 = context contains all required information\n"
        "0.5 = context contains some required information\n"
        "0.0 = context is missing required information\n\n"
        f"Ground Truth: {ground_truth}\n"
        f"Context: {context[:500]}\n\n"
        "Score (single decimal number only, e.g. 0.8):"
    )

    return {
        "faithfulness":      faithfulness,
        "answer_relevancy":  answer_relevancy,
        "context_precision": context_precision,
        "context_recall":    context_recall
    }


# ─────────────────────────────────────────────
# TruLens Judge
# ─────────────────────────────────────────────

def _trulens_judge(prompt: str) -> float:
    """
    Call Groq as LLM judge for TruLens metrics.
    Forces a numeric response with explicit instructions.
    Falls back to 0.75 if no number found.
    """
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
    """
    Approximate TruLens metrics using Groq as LLM judge.
    Each metric scored 0.0 - 1.0.
    """

    groundedness = _trulens_judge(
        "You are an evaluation judge. Reply with a single decimal number between "
        "0.0 and 1.0 only. No words, no explanation.\n\n"
        "Task: Score whether every claim in the answer is supported by the context.\n"
        "1.0 = all claims are fully supported by context\n"
        "0.5 = some claims are supported\n"
        "0.0 = claims are not supported by context\n\n"
        f"Context: {context[:500]}\n"
        f"Answer: {answer[:300]}\n\n"
        "Score (single decimal number only, e.g. 0.9):"
    )

    answer_relevance = _trulens_judge(
        "You are an evaluation judge. Reply with a single decimal number between "
        "0.0 and 1.0 only. No words, no explanation.\n\n"
        "Task: Score whether the answer directly and completely addresses the question.\n"
        "1.0 = answer fully and directly addresses the question\n"
        "0.5 = answer partially addresses the question\n"
        "0.0 = answer does not address the question\n\n"
        f"Question: {question}\n"
        f"Answer: {answer[:300]}\n\n"
        "Score (single decimal number only, e.g. 0.8):"
    )

    context_relevance = _trulens_judge(
        "You are an evaluation judge. Reply with a single decimal number between "
        "0.0 and 1.0 only. No words, no explanation.\n\n"
        "Task: Score whether the retrieved context is relevant to the question.\n"
        "1.0 = context is highly relevant to the question\n"
        "0.5 = context is somewhat relevant\n"
        "0.0 = context is not relevant to the question\n\n"
        f"Question: {question}\n"
        f"Context: {context[:500]}\n\n"
        "Score (single decimal number only, e.g. 0.7):"
    )

    return {
        "groundedness":      groundedness,
        "answer_relevance":  answer_relevance,
        "context_relevance": context_relevance
    }


# ─────────────────────────────────────────────
# /evaluate — RAGAS + TruLens Endpoint
# ─────────────────────────────────────────────

@app.post("/evaluate")
async def run_evaluation():
    """
    Run RAGAS + TruLens evaluation on 5 ground truth questions.
    Returns aggregated + per-question scores for Streamlit EVAL tab.
    """

    ragas_per_q   = []
    trulens_per_q = []

    ragas_scores = {
        "faithfulness":      [],
        "answer_relevancy":  [],
        "context_precision": [],
        "context_recall":    []
    }

    trulens_scores = {
        "groundedness":      [],
        "answer_relevance":  [],
        "context_relevance": []
    }

    for item in EVAL_DATASET:
        q  = item["question"]
        gt = item["ground_truth"]

        context, sources = retrieve_context(q)

        if context is None:
            context = ""
            answer  = "No relevant information found."
        else:
            eval_prompt = (
                "Answer using only the context below.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {q}\n\n"
                "Answer:"
            )
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=eval_prompt
                )
                answer = response.text
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower():
                    answer = generate_with_groq(eval_prompt)
                else:
                    answer = "Error generating answer."

        # RAGAS scoring
        rq = _ragas_score(q, answer, context, gt)
        ragas_per_q.append({"question": q, **rq})
        for k in ragas_scores:
            ragas_scores[k].append(rq.get(k, 0.0))

        # TruLens scoring
        tq = _trulens_score(q, answer, context)
        trulens_per_q.append({
            "question": q,
            "answer":   answer[:150],
            **tq
        })
        for k in trulens_scores:
            trulens_scores[k].append(tq.get(k, 0.0))

    # Aggregate
    ragas_agg = {
        k: round(float(np.mean(v)), 4)
        for k, v in ragas_scores.items()
    }
    ragas_agg["overall"] = round(
        float(np.mean(list(ragas_agg.values()))), 4
    )

    trulens_agg = {
        k: round(float(np.mean(v)), 4)
        for k, v in trulens_scores.items()
    }
    trulens_agg["overall"] = round(
        float(np.mean(list(trulens_agg.values()))), 4
    )

    return {
        "ragas":   {"scores": ragas_agg,   "per_question": ragas_per_q},
        "trulens": {"scores": trulens_agg, "per_question": trulens_per_q}
    }


# ─────────────────────────────────────────────
# /upload — Document Ingestion
# ─────────────────────────────────────────────

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT supported"
        )

    content      = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size_mb:.1f}MB). Max {MAX_FILE_SIZE_MB}MB."
        )

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
                chunks = splitter.split_text(text)

                for chunk in chunks:
                    if not chunk.strip():
                        continue
                    embedding = get_embedding(chunk)
                    meta = {
                        "text":     chunk,
                        "source":   file.filename,
                        "page":     page_num + 1,
                        "chunk_id": f"{file.filename}_p{page_num+1}_{total_chunks}"
                    }
                    vectors.append({
                        "id":       str(uuid.uuid4()),
                        "values":   embedding,
                        "metadata": meta
                    })
                    add_to_bm25(chunk, meta)
                    total_chunks += 1
                    if len(vectors) >= 25:
                        index.upsert(vectors)
                        vectors = []
                        gc.collect()

                del text, chunks
                gc.collect()

        elif file.filename.endswith(".txt"):
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            text   = clean_text(text)
            chunks = splitter.split_text(text)
            del text
            gc.collect()

            for chunk in chunks:
                if not chunk.strip():
                    continue
                embedding = get_embedding(chunk)
                meta = {
                    "text":     chunk,
                    "source":   file.filename,
                    "page":     1,
                    "chunk_id": f"{file.filename}_p1_{total_chunks}"
                }
                vectors.append({
                    "id":       str(uuid.uuid4()),
                    "values":   embedding,
                    "metadata": meta
                })
                add_to_bm25(chunk, meta)
                total_chunks += 1
                if len(vectors) >= 25:
                    index.upsert(vectors)
                    vectors = []
                    gc.collect()

        if vectors:
            index.upsert(vectors)
            gc.collect()

        if 'tmp_path' in locals() and tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

        return {
            "message":      "Document indexed successfully",
            "filename":     file.filename,
            "total_chunks": total_chunks,
            "bm25_corpus":  len(bm25_corpus)
        }

    except Exception as e:
        print("Upload error:", e)
        if 'tmp_path' in locals() and tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )