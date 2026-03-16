"""
Enterprise GenAI Knowledge Assistant
RAG System with:
- Gemini embeddings
- Pinecone vector DB
- Multi-query retrieval
- Gemini LLM (primary)
- Groq fallback
- Document upload
"""

import os
import gc
import uuid
import tempfile
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai
from pinecone import Pinecone
from groq import Groq

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ------------------------------------------------
# Load environment
# ------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

INDEX_NAME = "enterprise-rag-index"


# ------------------------------------------------
# Clients
# ------------------------------------------------

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


# ------------------------------------------------
# FastAPI
# ------------------------------------------------

app = FastAPI(
    title="Enterprise GenAI Assistant",
    version="3.0"
)

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
    question: str
    session_id: str


# ------------------------------------------------
# Session memory
# ------------------------------------------------

chat_memory = {}


# ------------------------------------------------
# Text splitter
# ------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)


# ------------------------------------------------
# Embedding
# ------------------------------------------------

def get_embedding(text):

    result = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values


# ------------------------------------------------
# Query rewriting
# ------------------------------------------------

def generate_search_queries(question):

    try:

        prompt = f"""
Generate 3 different search queries for retrieving documents
related to this question.

Question: {question}

Queries:
"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content

        queries = [
            q.strip("- ").strip()
            for q in text.split("\n")
            if q.strip()
        ]

        queries.append(question)

        return queries[:4]

    except Exception as e:

        print("Query rewrite error:", e)

        return [question]


# ------------------------------------------------
# Retrieve context
# ------------------------------------------------

def retrieve_context(question):

    queries = generate_search_queries(question)

    all_chunks = []
    all_sources = []

    for q in queries:

        query_embedding = get_embedding(q)

        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )

        for match in results.matches:

            if match.score > 0.3:

                metadata = match.metadata

                text = metadata.get("text", "")
                source = metadata.get("source", "")
                page = metadata.get("page", "")

                if text:

                    all_chunks.append(text)

                    all_sources.append({
                        "text": text,
                        "source": source,
                        "page": page
                    })

    unique_chunks = list(dict.fromkeys(all_chunks))

    context = "\n\n".join(unique_chunks[:5])

    return context, all_sources[:5]


# ------------------------------------------------
# Groq fallback
# ------------------------------------------------

def generate_with_groq(prompt):

    try:

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Answer using provided company documents."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print("Groq error:", e)

        return "⚠️ Backup AI model failed."


# ------------------------------------------------
# Ask endpoint
# ------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question
    session_id = request.session_id

    try:

        history = chat_memory.get(session_id, [])
        history_text = "\n".join(history)

        context, sources = retrieve_context(question)

        if not context:
            return {
                "answer": "No relevant information found in the knowledge base.",
                "sources": [],
                "session_id": session_id
            }

        prompt = f"""
Use the context below to answer the question.

Context:
{context}

Conversation History:
{history_text}

Question:
{question}

Answer:
"""

        try:

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            answer = response.text

        except Exception as e:

            err = str(e)

            print("Gemini error:", err)

            if "429" in err or "RESOURCE_EXHAUSTED" in err:

                print("Switching to Groq fallback")

                answer = generate_with_groq(prompt)

            else:

                answer = "⚠️ AI processing error."

        history.append(f"User: {question}")
        history.append(f"Assistant: {answer}")

        chat_memory[session_id] = history

        return {
            "answer": answer,
            "sources": sources,
            "session_id": session_id
        }

    except Exception as e:

        print("ERROR in /ask:", e)

        raise HTTPException(
            status_code=500,
            detail="Internal RAG pipeline error"
        )


# ------------------------------------------------
# Upload endpoint
# ------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT supported"
        )

    content = await file.read()

    tmp_path = None
    total_chunks = 0
    vectors = []

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

                if not text:
                    continue

                chunks = splitter.split_text(text)

                for chunk in chunks:

                    embedding = get_embedding(chunk)

                    vectors.append({
                        "id": str(uuid.uuid4()),
                        "values": embedding,
                        "metadata": {
                            "text": chunk,
                            "source": file.filename,
                            "page": page_num + 1
                        }
                    })

                    total_chunks += 1

                    if len(vectors) >= 25:

                        index.upsert(vectors)
                        vectors = []
                        gc.collect()

        if vectors:
            index.upsert(vectors)

        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

        return {
            "message": "Document indexed successfully",
            "chunks": total_chunks
        }

    except Exception as e:

        print("Upload error:", e)

        raise HTTPException(
            status_code=500,
            detail="Upload failed"
        )