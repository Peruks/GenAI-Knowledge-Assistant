<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=NEXUS&fontSize=80&fontColor=ffffff&fontAlignY=35&desc=Enterprise%20Knowledge%20OS&descAlignY=55&descSize=22&animation=fadeIn" width="100%"/>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Live%20%26%20Active-10C880?style=for-the-badge&logo=statuspage&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Pinecone-Vector%20DB-5B7FFF?style=for-the-badge&logo=pinecone&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-Primary%20LLM-F55036?style=for-the-badge&logo=groq&logoColor=white"/>
  <img src="https://img.shields.io/badge/NVIDIA-NIM%20Fallback-76B900?style=for-the-badge&logo=nvidia&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B35?style=for-the-badge&logo=langchain&logoColor=white"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/RAGAS-0.75%20FAIR-F59E0B?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/TruLens-0.62%20FAIR-8B5CF6?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=for-the-badge&logo=railway&logoColor=white"/>
</p>

<p align="center">
  <a href="https://ai-rag-llm.streamlit.app/" target="_blank">
    <img src="https://img.shields.io/badge/🚀%20Live%20Demo-ai--rag--llm.streamlit.app-5B7FFF?style=for-the-badge"/>
  </a>
</p>

<br/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=3000&pause=800&color=00E5FF&center=true&vCenter=true&multiline=true&width=700&height=80&lines=Hybrid+RAG+%2B+BM25+%2B+Vector+%2B+RRF+Fusion;LangGraph+4-Agent+with+Human-in-the-Loop;RAGAS+%2B+TruLens+Evaluation+Dashboard" alt="Typing SVG"/>

</div>

---

## ⬡ What is NEXUS?

**NEXUS** is a production-grade **Enterprise Knowledge Assistant** built on a full hybrid RAG pipeline with multi-agent orchestration, LLM evaluation, and cloud deployment. It allows organisations to upload company documents and ask natural language questions — getting accurate, grounded answers with source citations and full retrieval transparency.

Built entirely from scratch as a portfolio GenAI engineering project demonstrating production-level skills across the full stack: embeddings, hybrid search, LLM orchestration, multi-agent workflows, evaluation pipelines, and cloud deployment.

> **Try it live →** [ai-rag-llm.streamlit.app](https://ai-rag-llm.streamlit.app/)

---

## ✨ Features

<table>
<tr>
<td width="50%">

**🔍 Hybrid Retrieval**
- BM25 keyword search + Pinecone vector search
- Reciprocal Rank Fusion (RRF) merges both results
- Multi-query rewriting via Groq (3 variants per question)
- Guardrail score threshold (0.30) filters noise
- 3072-dimensional embeddings via gemini-embedding-001

</td>
<td width="50%">

**🤖 3-way LLM Fallback**
- Groq llama-3.1-8b-instant as primary (14,400 req/day)
- NVIDIA NIM llama-3.1-8b as fallback 1 (separate quota)
- Gemini 2.5 Flash as fallback 2 (last resort)
- Silent automatic switching — zero user impact
- Streaming SSE with per-provider fallback

</td>
</tr>
<tr>
<td width="50%">

**🧠 LangGraph 4-Agent Pipeline**
- Planner → generates targeted search queries
- Retriever → pure BM25 + Vector (no LLM quota used)
- Validator → NVIDIA NIM scores context sufficiency
- Answer → Groq generates grounded response
- Clarifier → human-in-the-loop when context insufficient

</td>
<td width="50%">

**📊 RAG Evaluation Dashboard**
- RAGAS: Faithfulness, Answer Relevancy, Context Precision, Context Recall
- TruLens: Groundedness, Answer Relevance, Context Relevance
- Groq as LLM judge — no extra API needed
- Live evaluation UI with per-question breakdown
- Score bars with color-coded quality levels

</td>
</tr>
<tr>
<td width="50%">

**📄 Document Ingestion**
- Upload PDF or TXT via the UI
- Section-aware chunking — splits at numbered headings
- Memory-safe page-by-page PDF processing
- Batch upserts of 25 vectors at a time
- Indexed in both Pinecone and BM25 simultaneously

</td>
<td width="50%">

**⚡ Production Infrastructure**
- FastAPI backend — Railway (primary), Render (backup)
- Streamlit Cloud frontend
- Docker containerized — python:3.11-slim, non-root user
- LangChain LCEL RetrievalQA chain (/ask-lc)
- 5 API endpoints with full Swagger docs at /docs

</td>
</tr>
</table>

---

## 🏗️ Architecture

### Standard Hybrid RAG Pipeline

```
User Query
    ↓
Multi-Query Rewriting (Groq) — generates 3 search variants
    ↓
┌─────────────────────────────────────────────────────┐
│              HYBRID RETRIEVAL                        │
│  Vector Search (Pinecone)  +  BM25 Keyword Search   │
│  gemini-embedding-001           rank-bm25 in-memory │
└──────────────────┬──────────────────────────────────┘
                   ↓
    Reciprocal Rank Fusion (RRF) — merges both result lists
                   ↓
    Guardrail Filter — score threshold 0.30
                   ↓
    Context Assembly — top-5 chunks joined
                   ↓
┌─────────────────────────────────────────────────────┐
│              LLM GENERATION                          │
│  Groq (primary) → NVIDIA NIM → Gemini 2.5 Flash     │
└──────────────────┬──────────────────────────────────┘
                   ↓
    Answer + Source Citations
```

### LangGraph Multi-Agent Pipeline

```
User Query
    ↓
[PLANNER / Groq]
    → Classifies intent (factual/procedural/policy)
    → Picks strategy (specific/broad/multi-aspect)
    → Generates 3 targeted sub-queries
    ↓
[RETRIEVER / No LLM]
    → BM25 + Vector hybrid search
    → RRF fusion across all sub-queries
    → Zero API quota consumed
    ↓
[VALIDATOR / NVIDIA NIM]
    → Scores context sufficiency (0.0 – 1.0)
    → Score ≥ 0.5 → route to Answer
    → Score < 0.5 → route to Clarifier
    ↓
[ANSWER / Groq → Gemini fallback]     [CLARIFIER / Groq]
    → Grounded response generation         → Human-in-the-loop
    → Full source citations                → Asks clarifying question
    ↓
Answer + Agent Execution Trace + Validation Score
```

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology | Details |
|:------|:-----------|:--------|
| 🖥️ **Frontend** | Streamlit Cloud | 4-tab UI · Agent trace panel · Eval dashboard |
| ⚙️ **Backend** | FastAPI + Uvicorn | Railway · 6 endpoints · Swagger at /docs |
| 🐳 **Container** | Docker | python:3.11-slim · non-root · healthcheck |
| 🗄️ **Vector DB** | Pinecone Serverless | 3072-dim · cosine · top-k retrieval |
| 🔤 **Keyword** | rank-bm25 | In-memory · warmed from Pinecone on startup |
| 🔀 **Fusion** | Reciprocal Rank Fusion | Merges vector + BM25 result lists |
| 🧠 **Embedding** | gemini-embedding-001 | Google Gemini API · 3072-dim vectors |
| 🤖 **LLM Primary** | Groq llama-3.1-8b-instant | 14,400 req/day free · fastest inference |
| 🔄 **LLM Fallback 1** | NVIDIA NIM llama-3.1-8b | build.nvidia.com · separate quota |
| 🔄 **LLM Fallback 2** | Gemini 2.5 Flash | Google AI Studio · last resort |
| 🔗 **Orchestration** | LangChain LCEL + LangGraph | RetrievalQA chain + 4-agent StateGraph |
| ✂️ **Chunking** | Section-aware + Recursive | Splits at section headings first |
| 📊 **Evaluation** | RAGAS + TruLens | Groq as LLM judge · live dashboard |

</div>

---

## 📁 Project Structure

```
enterprise-genai-assistant/
│
├── app/
│   ├── api/
│   │   └── rag_api.py              # FastAPI v4.3 — all 6 endpoints
│   │
│   ├── rag/
│   │   ├── store_embeddings.py     # Multi-file section-aware indexing
│   │   ├── langchain_rag.py        # LangChain LCEL chain (/ask-lc)
│   │   └── langgraph_agent.py      # LangGraph 4-agent pipeline (/ask-agent)
│   │
│   └── evaluation/
│       ├── eval_dataset.py         # 5 ground truth Q&A pairs
│       ├── ragas_eval.py           # RAGAS local runner
│       └── trulens_eval.py         # TruLens local runner
│
├── data/
│   └── company_policy.txt          # Sample 10-section company policy
│
├── .github/
│   └── workflows/                  # CI/CD (coming soon)
│
├── streamlit_app.py                # Frontend — chat, ingest, eval, system tabs
├── requirements.txt                # Full dependencies (Railway)
├── requirements-render.txt         # Lightweight (Render backup)
├── Dockerfile                      # Container config
├── render.yaml                     # Render deployment
└── README.md
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/` | GET | Health check · version · BM25 corpus count |
| `/ask` | POST | Custom hybrid RAG pipeline |
| `/ask-stream` | POST | SSE streaming responses |
| `/ask-lc` | POST | LangChain LCEL RetrievalQA chain |
| `/ask-agent` | POST | LangGraph 4-agent pipeline with trace |
| `/upload` | POST | Document ingestion (PDF + TXT) |
| `/evaluate` | POST | RAGAS + TruLens evaluation run |

Full Swagger docs: `https://genai-knowledge-api-production.up.railway.app/docs`

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.11+
Pinecone account (free tier)
Google AI Studio API key (Gemini — free)
Groq API key (free)
NVIDIA API key (build.nvidia.com — free)
```

### 1. Clone & setup

```bash
git clone https://github.com/Peruks/GenAI-Knowledge-Assistant.git
cd GenAI-Knowledge-Assistant

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

### 2. Environment variables

Create `.env` in root:

```env
PINECONE_API_KEY=your_pinecone_key
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
NVIDIA_API_KEY=your_nvidia_key
```

### 3. Index documents

```bash
python clear_index.py                  # clear existing vectors
python app/rag/store_embeddings.py     # index with section-aware chunking
```

### 4. Run locally

```bash
uvicorn app.api.rag_api:app --reload   # backend at localhost:8000
streamlit run streamlit_app.py         # frontend at localhost:8501
```

### 5. Docker

```bash
docker build -t nexus-api .
docker run -p 8000:8000 --env-file .env nexus-api
```

---

## ⚙️ Configuration

| Variable | Description | Default |
|:---------|:------------|:--------|
| `PINECONE_API_KEY` | Pinecone API key | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `GROQ_API_KEY` | Groq API key — primary LLM | Required |
| `NVIDIA_API_KEY` | NVIDIA NIM API key — fallback 1 | Required |
| `INDEX_NAME` | Pinecone index name | `enterprise-rag-index` |
| `MAX_FILE_SIZE_MB` | Max upload file size | `10` |
| `chunk_size` | Fallback chunk size (tokens) | `500` |
| `top_k` | Chunks retrieved per query | `5` |
| `score_threshold` | Guardrail filter score | `0.30` |

---

## 🔧 Engineering Decisions

<details>
<summary><b>Why Groq as primary LLM instead of Gemini?</b></summary>

Gemini's free tier has a daily quota that runs out during demo traffic or heavy testing. Groq offers **14,400 requests/day** on llama-3.1-8b-instant — far more generous. Groq is also consistently faster (sub-second latency). The result: Groq handles nearly all traffic, NVIDIA provides a second independent quota, and Gemini is preserved as last resort only.

</details>

<details>
<summary><b>Why NVIDIA NIM as fallback instead of OpenAI?</b></summary>

NVIDIA NIM uses the same OpenAI-compatible API format — zero extra code. The free tier at build.nvidia.com provides a separate quota pool completely independent from Groq. Using three providers with independent quotas means the system can sustain much higher traffic before any user sees an error. OpenAI requires a paid key; NVIDIA does not.

</details>

<details>
<summary><b>Why Reciprocal Rank Fusion over weighted scores?</b></summary>

Vector scores and BM25 scores use completely different scales — cosine similarity (0 to 1) vs BM25 (0 to ∞). Normalising them and combining with weights requires tuning. RRF avoids this entirely — it only uses rank positions, which are always comparable. A chunk ranked 2nd by vector search and 1st by BM25 gets a combined RRF score that correctly reflects it appeared near the top of both lists.

</details>

<details>
<summary><b>Why section-aware chunking over fixed 500-token chunks?</b></summary>

Fixed chunks frequently cross section boundaries — one chunk ends mid-sentence about sick leave and starts the next section about passwords. When a user asks about sick leave, the retrieved chunk contains unrelated password content. This directly tanks Context Relevance scores. Section-aware chunking splits at numbered headings and ALL CAPS boundaries first, so each chunk stays within one complete topic.

</details>

<details>
<summary><b>Why Groq as evaluation judge instead of RAGAS/TruLens libraries?</b></summary>

Installing `ragas` and `trulens-eval` on Railway free tier would push memory usage past the 512MB limit. Instead, the evaluation endpoint calls Groq with structured judge prompts that replicate the same scoring logic. This achieves the same evaluation quality with zero additional dependencies — the entire system stays under 200MB deployed.

</details>

<details>
<summary><b>Why LangGraph Retriever agent uses no LLM?</b></summary>

The Retriever agent only needs to run BM25 + vector search — a purely computational operation. Adding an LLM call here would waste quota and add latency for no reason. The Planner already handled query generation. The Validator handles quality scoring. The Retriever's only job is search, which needs zero LLM involvement.

</details>

---

## 📊 Evaluation Results

| Metric | Score | Status |
|:-------|:------|:-------|
| **RAGAS Faithfulness** | 0.80 | 🟢 STRONG |
| **RAGAS Answer Relevancy** | 0.75 | 🟡 FAIR |
| **RAGAS Context Precision** | 0.74 | 🟡 FAIR |
| **RAGAS Context Recall** | 0.72 | 🟡 FAIR |
| **RAGAS Overall** | **0.75** | 🟡 FAIR |
| **TruLens Groundedness** | 0.82 | 🟢 STRONG |
| **TruLens Answer Relevance** | 0.75 | 🟡 FAIR |
| **TruLens Context Relevance** | 0.80 | 🟢 STRONG |
| **TruLens Overall** | **0.79** | 🟡 FAIR |

*Evaluated on 5 ground truth Q&A pairs · Groq llama-3.1-8b as judge*

---

## 🗺️ Roadmap

- [x] Core RAG pipeline with Pinecone + Gemini embeddings
- [x] Hybrid Retrieval — BM25 + Vector + RRF fusion
- [x] Multi-query rewriting
- [x] 3-way LLM fallback — Groq → NVIDIA NIM → Gemini
- [x] Streaming SSE responses
- [x] Section-aware document chunking
- [x] Document upload — PDF + TXT, memory-safe
- [x] LangChain LCEL RetrievalQA chain
- [x] LangGraph 4-agent pipeline with human-in-the-loop
- [x] RAGAS evaluation pipeline
- [x] TruLens quality tracing
- [x] Live evaluation dashboard in UI
- [x] Docker containerization
- [x] Railway + Render deployment
- [ ] CI/CD GitHub Actions
- [ ] Redis persistent conversation memory
- [ ] Multi-document source filtering
- [ ] Cross-encoder re-ranking
- [ ] DOCX / HTML / CSV ingestion

---

## 🚢 Deployment

### Backend — Railway (Primary)

```bash
# Connect GitHub repo to Railway
# Set environment variables in Railway dashboard:
PINECONE_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, NVIDIA_API_KEY

# Railway auto-deploys on every git push via Dockerfile
```

### Frontend — Streamlit Cloud

```bash
# Connect GitHub repo at share.streamlit.io
# Main file: streamlit_app.py
# Add secrets: same 4 env vars above
```

### Backup Backend — Render

```bash
# Uses requirements-render.txt (no LangChain — lighter build)
# render.yaml already configured
# /ask, /ask-stream, /upload, /evaluate all work
# /ask-lc returns graceful error (LangChain not installed)
```

---

## 📄 License

Open source under the [MIT License](LICENSE).

---

<div align="center">

**Built by [@Perarivalan](https://github.com/Peruks)**

<p>
  <a href="https://ai-rag-llm.streamlit.app/">
    <img src="https://img.shields.io/badge/🚀%20Live%20Demo-Try%20it%20now-00E5FF?style=for-the-badge"/>
  </a>
  &nbsp;
  <a href="https://github.com/Peruks">
    <img src="https://img.shields.io/badge/GitHub-Peruks-181717?style=for-the-badge&logo=github&logoColor=white"/>
  </a>
</p>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

</div>