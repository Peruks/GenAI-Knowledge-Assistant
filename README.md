<div align="center">

<!-- Animated header banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=NEXUS&fontSize=80&fontColor=ffffff&fontAlignY=35&desc=Enterprise%20Knowledge%20OS&descAlignY=55&descSize=22&animation=fadeIn" width="100%"/>

<!-- Badges row 1 -->
<p align="center">
  <img src="https://img.shields.io/badge/Status-Live%20%26%20Active-10C880?style=for-the-badge&logo=statuspage&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
</p>

<!-- Badges row 2 -->
<p align="center">
  <img src="https://img.shields.io/badge/Pinecone-Vector%20DB-5B7FFF?style=for-the-badge&logo=pinecone&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-Fallback%20LLM-F55036?style=for-the-badge&logo=groq&logoColor=white"/>
  <img src="https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=for-the-badge&logo=railway&logoColor=white"/>
</p>

<!-- Live demo button -->
<p align="center">
  <a href="https://ai-rag-llm.streamlit.app/" target="_blank">
    <img src="https://img.shields.io/badge/🚀%20Live%20Demo-ai--rag--llm.streamlit.app-5B7FFF?style=for-the-badge"/>
  </a>
</p>

<br/>

<!-- Animated typing effect via readme-typing-svg -->
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=3000&pause=800&color=5B7FFF&center=true&vCenter=true&multiline=true&width=650&height=80&lines=Ask+questions+about+your+documents;Get+grounded+answers+with+source+citations;Powered+by+RAG+%2B+Vector+Search+%2B+Gemini" alt="Typing SVG"/>

</div>

---

## ⬡ What is NEXUS?

**NEXUS** is a production-style **Enterprise Knowledge Assistant** built on a full RAG (Retrieval Augmented Generation) pipeline. It allows you to upload company documents and ask natural language questions — getting accurate, grounded answers with source citations.

Built entirely from scratch as a portfolio-level GenAI engineering project demonstrating real-world skills: embeddings, vector databases, LLM orchestration, memory-safe ingestion, fallback systems, and cloud deployment.

> **Try it live →** [ai-rag-llm.streamlit.app](https://ai-rag-llm.streamlit.app/)

---

## ✨ Features

<table>
<tr>
<td width="50%">

**🔍 Smart Retrieval**
- Cosine similarity vector search via Pinecone
- Top-k=5 chunk retrieval per query
- Guardrail score threshold (0.30) filters noise
- 3072-dimensional embeddings via Gemini

</td>
<td width="50%">

**📄 Document Ingestion**
- Upload PDF or TXT through the UI
- Page-by-page memory-safe processing
- Batch upserts of 25 vectors at a time
- Automatic chunking at 500 tokens

</td>
</tr>
<tr>
<td width="50%">

**🤖 Dual LLM System**
- Gemini 2.5 Flash as primary LLM
- Groq llama-3.1-8b-instant as silent fallback
- Automatic switching on quota exceeded
- Zero user impact during failover

</td>
<td width="50%">

**💬 Conversational Memory**
- Session-based conversation history
- Multi-turn context maintained per session
- Unique session IDs per browser session
- Clear session functionality

</td>
</tr>
<tr>
<td width="50%">

**📎 Source Citations**
- Every answer includes retrieved chunks
- Expandable source viewer
- Chunk index and content shown
- Full transparency on answer grounding

</td>
<td width="50%">

**⚡ Production Ready**
- Deployed on Railway (backend)
- Deployed on Streamlit Cloud (frontend)
- CORS-enabled FastAPI backend
- Response latency tracking

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEXUS RAG PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   User Query                                                      │
│       │                                                           │
│       ▼                                                           │
│   ┌─────────────────────────────┐                                 │
│   │   Gemini Embedding API      │  ← gemini-embedding-001         │
│   │   Query → 3072-dim vector   │     (Google Gemini)             │
│   └─────────────┬───────────────┘                                 │
│                 │                                                  │
│                 ▼                                                  │
│   ┌─────────────────────────────┐                                 │
│   │   Pinecone Vector Search    │  ← Serverless Index             │
│   │   Cosine similarity top-k=5 │     3072 dims · cosine          │
│   └─────────────┬───────────────┘                                 │
│                 │                                                  │
│                 ▼                                                  │
│   ┌─────────────────────────────┐                                 │
│   │   Guardrail Filter          │  ← Score threshold = 0.30       │
│   │   Drop irrelevant chunks    │     Removes noise               │
│   └─────────────┬───────────────┘                                 │
│                 │                                                  │
│                 ▼                                                  │
│   ┌─────────────────────────────┐                                 │
│   │   Context Assembly          │  ← Join top chunks              │
│   │   Build prompt with context │     Into structured prompt      │
│   └─────────────┬───────────────┘                                 │
│                 │                                                  │
│                 ▼                                                  │
│   ┌─────────────────────────────┐   ┌─────────────────────────┐   │
│   │   Gemini 2.5 Flash (Primary)│──▶│ Groq llama-3.1-8b       │   │
│   │   Generate grounded answer  │   │ (Silent Fallback)        │   │
│   └─────────────┬───────────────┘   └─────────────────────────┘   │
│                 │                                                  │
│                 ▼                                                  │
│        Answer + Source Citations                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology | Details |
|:------|:-----------|:--------|
| 🖥️ **Frontend** | Streamlit Cloud | Tab-based UI · Real-time metrics · Source viewer |
| ⚙️ **Backend** | FastAPI + Uvicorn | Railway free tier · CORS enabled · `/ask` + `/upload` |
| 🗄️ **Vector DB** | Pinecone Serverless | 3072 dims · Cosine metric · Top-k retrieval |
| 🧠 **Embedding** | gemini-embedding-001 | Google Gemini API · 3072-dimensional vectors |
| 🤖 **LLM Primary** | Gemini 2.5 Flash | Google AI Studio · Grounded generation |
| 🔄 **LLM Fallback** | Groq llama-3.1-8b-instant | Auto-failover on quota exceeded |
| ✂️ **Chunking** | RecursiveCharacterTextSplitter | chunk_size=500 · overlap=100 |
| 📄 **Parsing** | PyPDF + LangChain | PDF + TXT ingestion |

</div>

---

## 📁 Project Structure

```
enterprise-genai-assistant/
│
├── app/
│   ├── api/
│   │   └── rag_api.py              # FastAPI backend — /ask + /upload endpoints
│   │
│   ├── rag/
│   │   ├── rag_with_gemini.py      # Core RAG pipeline
│   │   ├── store_embeddings.py     # Embed and upsert documents to Pinecone
│   │   └── search_query.py         # Test search queries locally
│   │
│   └── ingestion/
│       └── load_documents.py       # Document loading utilities
│
├── data/
│   └── company_policy.txt          # Sample knowledge base document
│
├── streamlit_app.py                # Streamlit frontend — NEXUS UI
├── requirements.txt                # Python dependencies
├── render.yaml                     # Render deployment config (backup)
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.11+
Pinecone account (free tier)
Google AI Studio API key (free)
Groq API key (free)
```

### 1. Clone the repository

```bash
git clone https://github.com/Peruks/GenAI-Knowledge-Assistant.git
cd GenAI-Knowledge-Assistant
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the root:

```env
PINECONE_API_KEY=your_pinecone_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

### 5. Create Pinecone index

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your_pinecone_api_key")
pc.create_index(
    name="enterprise-rag-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

### 6. Index your documents

```bash
# Add your documents to data/ folder, then:
python app/rag/store_embeddings.py
```

### 7. Run the backend

```bash
uvicorn app.api.rag_api:app --reload
# API running at http://localhost:8000
```

### 8. Run the frontend

```bash
streamlit run streamlit_app.py
# UI running at http://localhost:8501
```

---

## 🔌 API Reference

### `POST /ask`

Ask a question against the knowledge base.

```json
// Request
{
  "question": "What is the leave policy?",
  "session_id": "user_123"
}

// Response
{
  "question": "What is the leave policy?",
  "answer": "Employees are entitled to 20 days of paid annual leave per year...",
  "sources": ["Employees are entitled to 20 days...", "Leave requests must be submitted..."],
  "session_id": "user_123"
}
```

### `POST /upload`

Upload and index a document.

```bash
curl -X POST "https://genai-knowledge-api-production.up.railway.app/upload" \
  -F "file=@company_policy.pdf"

# Response
{
  "message": "Document indexed successfully.",
  "filename": "company_policy.pdf",
  "total_chunks": 28
}
```

### `GET /`

Health check.

```json
{
  "message": "GenAI Knowledge Assistant API running",
  "version": "2.1",
  "llm_primary": "gemini-2.5-flash",
  "llm_fallback": "groq/llama-3.1-8b-instant"
}
```

---

## ⚙️ Configuration

| Variable | Description | Default |
|:---------|:------------|:--------|
| `PINECONE_API_KEY` | Pinecone API key | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `GROQ_API_KEY` | Groq API key for fallback | Required |
| `INDEX_NAME` | Pinecone index name | `enterprise-rag-index` |
| `MAX_FILE_SIZE_MB` | Max upload file size | `10` |
| `chunk_size` | Token size per chunk | `500` |
| `chunk_overlap` | Overlap between chunks | `100` |
| `top_k` | Number of chunks retrieved | `5` |
| `score_threshold` | Minimum relevance score | `0.30` |

---

## 🧠 How RAG Works

<details>
<summary><b>Click to expand — detailed explanation</b></summary>

**RAG (Retrieval Augmented Generation)** is a technique that grounds LLM responses in real documents rather than relying on training data alone.

**Step 1 — Indexing (done once)**
```
Document → Split into chunks → Embed each chunk → Store vectors in Pinecone
```

**Step 2 — Retrieval (every query)**
```
User question → Embed question → Find similar vectors → Return top chunks
```

**Step 3 — Generation**
```
Top chunks + User question → Build prompt → Send to LLM → Return grounded answer
```

**Why this matters:**
- LLMs hallucinate when asked about specific company data they've never seen
- RAG gives the LLM the exact relevant text at inference time
- The LLM's job becomes summarization + formatting, not memorization
- Source citations let users verify every answer

</details>

---

## 🔧 Engineering Decisions

<details>
<summary><b>Why Gemini Embedding over sentence-transformers?</b></summary>

`sentence-transformers` pulls PyTorch as a dependency (~2.5GB). Combined with other dependencies the total deployment size reached **6.5GB** — well over Railway and Render's free tier limits.

Switching to `gemini-embedding-001` via the Gemini API eliminates all local model files. Deployment size dropped to **under 100MB**. Zero PyTorch, zero GPU requirements, faster cold starts.

</details>

<details>
<summary><b>Why page-by-page PDF processing?</b></summary>

Loading a full PDF into memory at once caused **500 errors on large files** (17MB+ PDFs crashed the 512MB free-tier server). The solution: process one page at a time, embed chunks immediately, upsert in batches of 25, then call `gc.collect()` to free memory before the next page.

This keeps peak memory usage under 200MB even for large documents.

</details>

<details>
<summary><b>Why Groq as fallback?</b></summary>

Gemini's free tier has a daily request quota. During heavy testing or traffic spikes the quota runs out mid-session. Rather than showing an error, the system silently routes to **Groq's llama-3.1-8b-instant** which has a separate 14,400 requests/day free quota. Users never see the switch happen.

</details>

<details>
<summary><b>Why chunk_size=500 over the original 200?</b></summary>

Chunks of 200 tokens were too small to capture complete thoughts from policy documents. A single sentence about leave policy might span 150 tokens, leaving no room for context. Size 500 with overlap 100 captures full paragraphs while maintaining continuity across chunk boundaries.

</details>

---

## 🗺️ Roadmap

- [x] Core RAG pipeline with Pinecone + Gemini
- [x] Document upload (PDF + TXT)
- [x] Dual LLM fallback (Gemini → Groq)
- [x] Session-based conversational memory
- [x] Source citations and guardrail filtering
- [x] Production deployment (Railway + Streamlit Cloud)
- [ ] Hybrid Retrieval (BM25 + Vector search)
- [ ] Semantic chunking (boundary-aware splits)
- [ ] RAGAS evaluation pipeline
- [ ] Redis persistent conversation memory
- [ ] Streaming token responses
- [ ] LangGraph multi-agent workflow
- [ ] LangSmith observability and tracing
- [ ] DOCX / HTML / CSV ingestion support
- [ ] Authentication and rate limiting

---

## 🚢 Deployment

### Backend — Railway

```bash
# Connect GitHub repo to Railway
# Set environment variables in Railway dashboard:
PINECONE_API_KEY=...
GEMINI_API_KEY=...
GROQ_API_KEY=...

# Railway auto-deploys on every git push
```

### Frontend — Streamlit Cloud

```bash
# Connect GitHub repo at share.streamlit.io
# Set main file: streamlit_app.py
# Add secrets in app settings (same env vars)
```

### Backup Backend — Render

```yaml
# render.yaml already configured
# Free tier: 512MB RAM, cold starts after 15min inactivity
# Use Railway as primary (no cold start on free tier)
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/hybrid-retrieval`)
3. Commit your changes (`git commit -m 'Add BM25 hybrid retrieval'`)
4. Push to the branch (`git push origin feature/hybrid-retrieval`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

**Built by [@Perarivalan](https://github.com/Peruks)**

<p>
  <a href="https://ai-rag-llm.streamlit.app/">
    <img src="https://img.shields.io/badge/🚀%20Live%20Demo-Try%20it%20now-5B7FFF?style=for-the-badge"/>
  </a>
  &nbsp;
  <a href="https://github.com/Peruks">
    <img src="https://img.shields.io/badge/GitHub-Peruks-181717?style=for-the-badge&logo=github&logoColor=white"/>
  </a>
</p>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

</div>
