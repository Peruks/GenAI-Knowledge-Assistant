"""
Enterprise GenAI Knowledge Assistant
RAG System v4.0 with:
- Gemini embeddings
- Pinecone vector DB
- BM25 keyword search (Hybrid Retrieval)
- Reciprocal Rank Fusion (RRF)
- Multi-query retrieval
- Streaming responses
- Gemini LLM (primary)
- Groq fallback (streaming + non-streaming)
- Document upload
"""

import os
import gc
import uuid
import json
import tempfile
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

# BM25 for hybrid retrieval
from rank_bm25 import BM25Okapi


# ------------------------------------------------
# Load environment
# ------------------------------------------------

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")

INDEX_NAME       = "enterprise-rag-index"
MAX_FILE_SIZE_MB = 10


# ------------------------------------------------
# Clients
# ------------------------------------------------

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client   = Groq(api_key=GROQ_API_KEY)

pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


# ------------------------------------------------
# FastAPI
# ------------------------------------------------

app = FastAPI(title="Enterprise GenAI Assistant", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# Models
# ------------------------------------------------

class QuestionRequest(BaseModel):
    question:   str
    session_id: str


# ------------------------------------------------
# Session memory
# ------------------------------------------------

chat_memory = {}


# ------------------------------------------------
# BM25 in-memory corpus
# ------------------------------------------------

# Stores all chunks seen during this server session for BM25 search.
# Gets populated during /upload and pre-warmed at startup from Pinecone.
bm25_corpus      = []   # list of raw text strings
bm25_corpus_meta = []   # list of metadata dicts matching each corpus entry
bm25_index       = None # BM25Okapi instance, rebuilt when corpus changes


def rebuild_bm25():
    """Rebuild BM25 index from current corpus."""
    global bm25_index
    if bm25_corpus:
        tokenized = [doc.lower().split() for doc in bm25_corpus]
        bm25_index = BM25Okapi(tokenized)
    else:
        bm25_index = None


def add_to_bm25(text: str, metadata: dict):
    """Add a chunk to the BM25 corpus and rebuild index."""
    if text not in bm25_corpus:
        bm25_corpus.append(text)
        bm25_corpus_meta.append(metadata)
        rebuild_bm25()


# ------------------------------------------------
# Pre-warm BM25 from Pinecone at startup
# ------------------------------------------------

@app.on_event("startup")
def warmup_bm25():
    """
    On startup, fetch existing vectors from Pinecone
    and populate BM25 corpus so hybrid search works
    immediately without needing a fresh upload.
    """
    try:
        stats = index.describe_index_stats()
        total = stats.get("total_vector_count", 0)

        if total == 0:
            print("BM25 warmup: index is empty, skipping.")
            return

        # Fetch a dummy vector to get namespaces
        # Use list() to get IDs, then fetch metadata
        dummy_vec = [0.0] * 3072
        results = index.query(
            vector=dummy_vec,
            top_k=min(total, 200),   # fetch up to 200 chunks for BM25
            include_metadata=True
        )

        for match in results.matches:
            text = match.metadata.get("text", "")
            if text:
                add_to_bm25(text, match.metadata)

        print(f"BM25 warmup complete: {len(bm25_corpus)} chunks loaded.")

    except Exception as e:
        print(f"BM25 warmup error (non-fatal): {e}")


# ------------------------------------------------
# Text splitter
# ------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)


# ------------------------------------------------
# Embedding
# ------------------------------------------------

def get_embedding(text: str):
    result = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ------------------------------------------------
# Query rewriting
# ------------------------------------------------

def generate_search_queries(question: str):
    try:
        prompt = f"""Generate 3 different search queries for retrieving relevant documents about this question.
Return only the queries, one per line, no numbering or bullets.

Question: {question}

Queries:"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )

        text    = response.choices[0].message.content
        queries = [q.strip("- 0123456789.").strip() for q in text.split("\n") if q.strip()]
        queries.append(question)  # always include original
        return queries[:4]

    except Exception as e:
        print("Query rewrite error:", e)
        return [question]


# ------------------------------------------------
# Hybrid Retrieval — Vector + BM25 + RRF
# ------------------------------------------------

def vector_search(query: str, top_k: int = 5):
    """Pure vector search via Pinecone."""
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
    """BM25 keyword search over in-memory corpus."""
    if bm25_index is None or not bm25_corpus:
        return []

    tokenized_query = query.lower().split()
    scores          = bm25_index.get_scores(tokenized_query)

    # Get top-k indices sorted by score
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for i in top_indices:
        if scores[i] > 0:  # only include matches with positive score
            results.append({
                "text":     bm25_corpus[i],
                "metadata": bm25_corpus_meta[i],
                "score":    float(scores[i])
            })

    return results


def reciprocal_rank_fusion(vector_results, bm25_results, k: int = 60):
    """
    Merge vector and BM25 results using Reciprocal Rank Fusion.
    RRF score = sum(1 / (k + rank)) across result lists.
    Higher RRF score = more relevant.
    """
    rrf_scores = {}
    texts_map  = {}

    # Score vector results
    for rank, item in enumerate(vector_results):
        text = item["text"]
        rrf_scores[text]  = rrf_scores.get(text, 0) + 1 / (k + rank + 1)
        texts_map[text]   = item["metadata"]

    # Score BM25 results
    for rank, item in enumerate(bm25_results):
        text = item["text"]
        rrf_scores[text]  = rrf_scores.get(text, 0) + 1 / (k + rank + 1)
        texts_map[text]   = item["metadata"]

    # Sort by combined RRF score descending
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    return [
        {"text": text, "metadata": texts_map[text], "rrf_score": score}
        for text, score in ranked
    ]


def retrieve_context(question: str):
    """
    Hybrid retrieval pipeline:
    1. Generate multiple search queries
    2. For each query: vector search + BM25 search
    3. Merge all results with RRF
    4. Return top-5 unique chunks
    """
    queries = generate_search_queries(question)

    all_vector_results = []
    all_bm25_results   = []

    for q in queries:
        all_vector_results.extend(vector_search(q, top_k=3))
        all_bm25_results.extend(bm25_search(q, top_k=3))

    # Deduplicate within each result set before RRF
    seen_v = set()
    unique_vector = []
    for r in all_vector_results:
        if r["text"] not in seen_v:
            seen_v.add(r["text"])
            unique_vector.append(r)

    seen_b = set()
    unique_bm25 = []
    for r in all_bm25_results:
        if r["text"] not in seen_b:
            seen_b.add(r["text"])
            unique_bm25.append(r)

    # Fuse results
    fused = reciprocal_rank_fusion(unique_vector, unique_bm25)

    # Take top 5
    top = fused[:5]

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


# ------------------------------------------------
# LLM Generation helpers
# ------------------------------------------------

def build_prompt(question: str, context: str, history_text: str) -> str:
    return f"""You are an AI assistant answering questions using company documents.

Rules:
- Use ONLY the information from the context below
- Do NOT invent or assume information
- If the answer is not in the context say: "The information is not available in the provided documents"
- Keep answers clear and concise

Conversation History:
{history_text}

Context:
{context}

Question:
{question}

Answer:"""


def generate_with_groq(prompt: str) -> str:
    """Non-streaming Groq fallback."""
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
        return response.choices[0].message.content
    except Exception as e:
        print("Groq error:", e)
        return "Both AI models are currently unavailable. Please try again later."


# ------------------------------------------------
# Health check
# ------------------------------------------------

@app.get("/")
def root():
    return {
        "message":      "Enterprise GenAI Assistant API",
        "version":      "4.0",
        "retrieval":    "hybrid (vector + BM25 + RRF)",
        "llm_primary":  "gemini-2.5-flash",
        "llm_fallback": "groq/llama-3.1-8b-instant",
        "bm25_corpus":  len(bm25_corpus)
    }


# ------------------------------------------------
# /ask — Standard (non-streaming) endpoint
# ------------------------------------------------

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
                print("Switching to Groq fallback")
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


# ------------------------------------------------
# /ask-stream — Streaming endpoint (Phase 1)
# ------------------------------------------------

@app.post("/ask-stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Streaming version of /ask.
    Returns server-sent events (SSE) with tokens as they generate.
    Frontend reads chunks via requests stream=True.
    """

    question   = request.question
    session_id = request.session_id

    history      = chat_memory.get(session_id, [])
    history_text = "\n".join(history)

    context, sources = retrieve_context(question)

    # No context — stream a single message
    if context is None:
        async def no_context_stream():
            msg = "No relevant information found in the knowledge base."
            yield f"data: {json.dumps({'token': msg, 'done': False})}\n\n"
            yield f"data: {json.dumps({'sources': [], 'done': True})}\n\n"

        return StreamingResponse(
            no_context_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    prompt = build_prompt(question, context, history_text)

    async def stream_tokens():
        full_answer = ""

        # ── Gemini streaming ──
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
            print(f"Gemini stream error: {err}")

            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                print("Streaming fallback to Groq...")

                # ── Groq streaming fallback ──
                try:
                    full_answer = ""
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
                            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

                except Exception as groq_err:
                    msg = f"Both LLMs failed. Please try again."
                    yield f"data: {json.dumps({'token': msg, 'done': False})}\n\n"
                    full_answer = msg

            else:
                msg = "AI processing error. Please try again."
                yield f"data: {json.dumps({'token': msg, 'done': False})}\n\n"
                full_answer = msg

        # Update conversation memory
        history.append(f"User: {question}")
        history.append(f"Assistant: {full_answer}")
        chat_memory[session_id] = history

        # Final event with sources
        yield f"data: {json.dumps({'sources': sources, 'done': True})}\n\n"

    return StreamingResponse(
        stream_tokens(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ------------------------------------------------
# /upload — Document ingestion
# ------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF and TXT supported")

    content      = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size_mb:.1f}MB). Max {MAX_FILE_SIZE_MB}MB allowed."
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

                chunks = splitter.split_text(text)

                for chunk in chunks:
                    if not chunk.strip():
                        continue

                    embedding = get_embedding(chunk)
                    meta      = {
                        "text":     chunk,
                        "source":   file.filename,
                        "page":     page_num + 1,
                        "chunk_id": f"{file.filename}_p{page_num+1}_{total_chunks}"
                    }

                    vectors.append({
                        "id":     str(uuid.uuid4()),
                        "values": embedding,
                        "metadata": meta
                    })

                    # Also add to BM25 corpus
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

            chunks = splitter.split_text(text)
            del text
            gc.collect()

            for chunk in chunks:
                if not chunk.strip():
                    continue

                embedding = get_embedding(chunk)
                meta      = {
                    "text":     chunk,
                    "source":   file.filename,
                    "page":     1,
                    "chunk_id": f"{file.filename}_p1_{total_chunks}"
                }

                vectors.append({
                    "id":     str(uuid.uuid4()),
                    "values": embedding,
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
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")