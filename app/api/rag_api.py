"""
GenAI Knowledge Assistant API
RAG Pipeline with Guardrails + Document Upload
"""

import os
import gc
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

# Max file size: 20MB
MAX_FILE_SIZE_MB = 20


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
    return {
        "message": "GenAI Knowledge Assistant API running",
        "version": "2.0"
    }


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
        if score > 0.3:  # Relevance threshold
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
# 12. Upload Endpoint — Memory Safe
# ------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index PDF or TXT.
    - Page-by-page processing to stay within 512MB RAM
    - Batch upsert every 25 vectors
    - Explicit gc.collect() after each page
    - 10MB file size limit
    """

    # Validate file type
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    # Read file content
    content = await file.read()

    # Validate file size
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size_mb:.1f}MB). Maximum allowed is {MAX_FILE_SIZE_MB}MB. "
                   f"Please compress or split the file."
        )

    total_chunks = 0
    vectors = []
    tmp_path = None

    try:
        # Save to temp file
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Free content from memory
        del content
        gc.collect()

        # ---- Process PDF ----
        if file.filename.endswith(".pdf"):

            reader = PdfReader(tmp_path)
            total_pages = len(reader.pages)

            for page_num in range(total_pages):

                page = reader.pages[page_num]
                page_text = page.extract_text()

                if not page_text or not page_text.strip():
                    continue

                chunks = splitter.split_text(page_text)

                for chunk in chunks:
                    if not chunk.strip():
                        continue

                    embedding = get_embedding(chunk)

                    vectors.append({
                        "id": str(uuid.uuid4()),
                        "values": embedding,
                        "metadata": {
                            "text": chunk,
                            "source": file.filename,
                            "page": page_num + 1,
                            "chunk_id": f"{file.filename}_p{page_num + 1}_{total_chunks}"
                        }
                    })

                    total_chunks += 1

                    # Upsert every 25 vectors to keep memory low
                    if len(vectors) >= 25:
                        index.upsert(vectors)
                        vectors = []
                        gc.collect()

                # Free page from memory
                del page_text, chunks
                gc.collect()

        # ---- Process TXT ----
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

                vectors.append({
                    "id": str(uuid.uuid4()),
                    "values": embedding,
                    "metadata": {
                        "text": chunk,
                        "source": file.filename,
                        "page": 1,
                        "chunk_id": f"{file.filename}_p1_{total_chunks}"
                    }
                })

                total_chunks += 1

                if len(vectors) >= 25:
                    index.upsert(vectors)
                    vectors = []
                    gc.collect()

        # Upsert remaining vectors
        if vectors:
            index.upsert(vectors)
            vectors = []
            gc.collect()

        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

        return {
            "message": "Document indexed successfully.",
            "filename": file.filename,
            "total_chunks": total_chunks
        }

    except Exception as e:
        if 'tmp_path' in locals() and tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")