"""
GenAI Knowledge Assistant API
RAG Pipeline with Guardrails + Document Upload

Endpoints:
GET  /         - Health check
POST /ask      - RAG question answering
POST /upload   - Document upload and indexing
"""

import os
import uuid
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from google import genai
from pinecone import Pinecone
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ------------------------------------------------
# 1. Load Environment Variables
# ------------------------------------------------

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

INDEX_NAME = "enterprise-rag-index"


# ------------------------------------------------
# 2. Configure Gemini Client
# ------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)


# ------------------------------------------------
# 3. Pinecone Connection
# ------------------------------------------------

pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(INDEX_NAME)


# ------------------------------------------------
# 4. Text Splitter
# ------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)


# ------------------------------------------------
# 5. Embedding Function
# ------------------------------------------------

def get_embedding(text: str):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ------------------------------------------------
# 6. FastAPI App
# ------------------------------------------------

app = FastAPI(
    title="GenAI Knowledge Assistant",
    description="RAG-based AI assistant with guardrails and document upload",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# 7. Health Check
# ------------------------------------------------

@app.get("/")
def root():
    return {"message": "GenAI Knowledge Assistant API running", "version": "2.0"}


# ------------------------------------------------
# 8. Request Model
# ------------------------------------------------

class QuestionRequest(BaseModel):
    question: str
    session_id: str


# ------------------------------------------------
# 9. Conversation Memory
# ------------------------------------------------

chat_memory = {}


# ------------------------------------------------
# 10. Retrieve Context with Guardrails
# ------------------------------------------------

def retrieve_context(question: str):

    query_embedding = get_embedding(question)

    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    context_chunks = []
    sources = []

    for match in results["matches"]:
        score = match["score"]

        # Guardrail: only accept relevant chunks
        if score > 0.55:
            text = match["metadata"]["text"]
            context_chunks.append(text)
            sources.append(text)

    if not context_chunks:
        return None, []

    context = "\n".join(context_chunks)
    return context, sources


# ------------------------------------------------
# 11. Ask Endpoint
# ------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question
    session_id = request.session_id

    history = chat_memory.get(session_id, [])
    history_text = "\n".join(history)

    context, sources = retrieve_context(question)

    if context is None:
        return {
            "question": question,
            "answer": "No relevant information found in the knowledge base.",
            "sources": [],
            "session_id": session_id
        }

    prompt = f"""
You are an AI assistant answering questions using company documents.

Rules:
- Use ONLY the information from the context
- Do NOT invent information
- If the answer is not present say:
  "The information is not available in the provided documents"

Conversation History:
{history_text}

Context:
{context}

User Question:
{question}

Answer:
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    answer = response.text

    history.append(f"User: {question}")
    history.append(f"Assistant: {answer}")
    chat_memory[session_id] = history

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "session_id": session_id
    }


# ------------------------------------------------
# 12. Upload Endpoint (Memory-Safe)
# ------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a PDF or TXT document.
    Processes page-by-page to stay within 512MB RAM limit.
    """

    # Validate file type
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    total_chunks = 0
    vectors = []

    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # ---- Process PDF ----
        if file.filename.endswith(".pdf"):
            reader = PdfReader(tmp_path)
            total_pages = len(reader.pages)

            for page_num, page in enumerate(reader.pages):

                page_text = page.extract_text()

                if not page_text or not page_text.strip():
                    continue

                # Split page into chunks
                chunks = splitter.split_text(page_text)

                for chunk in chunks:
                    if not chunk.strip():
                        continue

                    embedding = get_embedding(chunk)

                    vector_id = str(uuid.uuid4())

                    vectors.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": {
                            "text": chunk,
                            "source": file.filename,
                            "page": page_num + 1
                        }
                    })

                    total_chunks += 1

                    # Batch upsert every 50 vectors to save memory
                    if len(vectors) >= 50:
                        index.upsert(vectors)
                        vectors = []

        # ---- Process TXT ----
        elif file.filename.endswith(".txt"):
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            chunks = splitter.split_text(text)

            for chunk in chunks:
                if not chunk.strip():
                    continue

                embedding = get_embedding(chunk)

                vector_id = str(uuid.uuid4())

                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "text": chunk,
                        "source": file.filename,
                        "page": 1
                    }
                })

                total_chunks += 1

                if len(vectors) >= 50:
                    index.upsert(vectors)
                    vectors = []

        # Upsert remaining vectors
        if vectors:
            index.upsert(vectors)

        # Cleanup temp file
        os.unlink(tmp_path)

        return {
            "message": "Document indexed successfully.",
            "filename": file.filename,
            "total_chunks": total_chunks
        }

    except Exception as e:
        # Cleanup on error
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")