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
# 2. Initialize Services
# ------------------------------------------------

# Gemini
genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel("gemini-2.5-flash")

# Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# Embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ------------------------------------------------
# 3. FastAPI App
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
# 4. Request Model
# ------------------------------------------------

class QuestionRequest(BaseModel):
    question: str
    session_id: str


# ------------------------------------------------
# 5. Conversational Memory
# ------------------------------------------------

chat_memory = {}


# ------------------------------------------------
# 6. Retrieve Context with Guardrails
# ------------------------------------------------

def retrieve_context(question):

    query_embedding = embedding_model.encode(question).tolist()

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
# 7. Ask Endpoint
# ------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question
    session_id = request.session_id

    # retrieve chat history
    history = chat_memory.get(session_id, [])

    history_text = "\n".join(history)

    # retrieve context
    context, sources = retrieve_context(question)

    # Guardrail: no context found
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

Follow these rules strictly:

1. Use ONLY the information from the provided context.
2. Do NOT invent information.
3. If the answer is not present in the context, say:
   "The information is not available in the provided documents."
4. Keep answers concise and clear.

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