"""
GenAI Knowledge Assistant API
RAG Pipeline with Guardrails

Pipeline:
User Question
    ↓
Gemini Embedding
    ↓
Vector Search (Pinecone)
    ↓
Context Filtering
    ↓
Gemini LLM
    ↓
Answer + Sources
"""

import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from google import genai
from pinecone import Pinecone


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
# 4. Gemini Embedding Function
# ------------------------------------------------

def get_embedding(text: str):

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values


# ------------------------------------------------
# 5. FastAPI App
# ------------------------------------------------

app = FastAPI(
    title="GenAI Knowledge Assistant",
    description="RAG based AI assistant with guardrails",
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
# 7. Conversation Memory
# ------------------------------------------------

chat_memory = {}


# ------------------------------------------------
# 8. Retrieve Context
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
        if score > -1:
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