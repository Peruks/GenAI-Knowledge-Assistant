"""
GenAI Knowledge Assistant API
RAG Pipeline with Guardrails

Pipeline:
User Question
    ↓
Embedding Model
    ↓
Vector Search (Pinecone)
    ↓
Context Filtering (Guardrail)
    ↓
Gemini LLM
    ↓
Answer + Sources
"""

import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import google.generativeai as genai


# ------------------------------------------------
# 1. Load Environment Variables
# ------------------------------------------------

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

INDEX_NAME = "enterprise-rag-index"


# ------------------------------------------------
# 2. Configure Gemini
# ------------------------------------------------

genai.configure(api_key=GEMINI_API_KEY)

llm = genai.GenerativeModel("gemini-2.5-flash")


# ------------------------------------------------
# 3. Lazy Load Pinecone
# ------------------------------------------------

pinecone_index = None


def get_pinecone_index():
    """
    Lazy load Pinecone index to reduce startup memory usage.
    """
    global pinecone_index

    if pinecone_index is None:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index(INDEX_NAME)

    return pinecone_index


# ------------------------------------------------
# 4. Lazy Load Embedding Model
# ------------------------------------------------

embedding_model = None


def get_embedding_model():
    """
    Lazy load embedding model.
    Prevents heavy torch loading during API startup.
    """
    global embedding_model

    if embedding_model is None:
        print("Loading embedding model...")
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return embedding_model


# ------------------------------------------------
# 5. FastAPI App
# ------------------------------------------------

app = FastAPI(
    title="GenAI Knowledge Assistant",
    description="RAG-based AI assistant with guardrails",
    version="1.0"
)


@app.get("/")
def root():
    return {"message": "GenAI Knowledge Assistant API running"}


# ------------------------------------------------
# 6. Request Model
# ------------------------------------------------

class QuestionRequest(BaseModel):
    question: str
    session_id: str


# ------------------------------------------------
# 7. Conversational Memory
# ------------------------------------------------

chat_memory = {}


# ------------------------------------------------
# 8. Retrieve Context with Guardrails
# ------------------------------------------------

def retrieve_context(question: str):

    model = get_embedding_model()

    query_embedding = model.encode(question).tolist()

    index = get_pinecone_index()

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
# 9. Ask Endpoint
# ------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question
    session_id = request.session_id

    # Retrieve chat history
    history = chat_memory.get(session_id, [])

    history_text = "\n".join(history)

    # Retrieve context
    context, sources = retrieve_context(question)

    # Guardrail: no relevant context
    if context is None:

        return {
            "question": question,
            "answer": "No relevant information found in the knowledge base.",
            "sources": [],
            "session_id": session_id
        }

    # Build prompt
    prompt = f"""
You are an AI assistant answering questions using company documents.

Rules:
1. Use ONLY the information from the provided context
2. Do NOT invent information
3. If the answer is not present say:
   "The information is not available in the provided documents"
4. Keep answers concise and clear

Conversation History:
{history_text}

Context:
{context}

User Question:
{question}

Answer:
"""

    response = llm.generate_content(prompt)

    answer = response.text

    # Update conversation memory
    history.append(f"User: {question}")
    history.append(f"Assistant: {answer}")

    chat_memory[session_id] = history

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "session_id": session_id
    }