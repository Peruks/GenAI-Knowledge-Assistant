"""
RAG Pipeline with Pinecone + Gemini

Pipeline Steps:
1. Convert user question into embedding
2. Retrieve relevant chunks from Pinecone
3. Build context from retrieved chunks
4. Send context + question to Gemini
5. Generate answer with sources
"""

import os
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

gemini_model = genai.GenerativeModel("gemini-2.5-flash")


# ------------------------------------------------
# 3. Pinecone Connection (Lazy Load)
# ------------------------------------------------

pinecone_index = None


def get_pinecone_index():
    """
    Lazy load Pinecone index.
    This prevents heavy initialization during server startup.
    """

    global pinecone_index

    if pinecone_index is None:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index(INDEX_NAME)

    return pinecone_index


# ------------------------------------------------
# 4. Embedding Model (Lazy Load)
# ------------------------------------------------

embedding_model = None


def get_embedding_model():
    """
    Lazy load embedding model.
    Model loads only when the first query arrives.
    """

    global embedding_model

    if embedding_model is None:
        print("Loading embedding model...")
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return embedding_model


# ------------------------------------------------
# 5. Main RAG Pipeline Function
# ------------------------------------------------

def ask_rag(question: str):
    """
    Main RAG pipeline.

    Input:
        question (str)

    Returns:
        answer (str)
        sources (list)
    """

    # ---------------------------------------------
    # Step 1: Convert question to embedding
    # ---------------------------------------------

    model = get_embedding_model()

    query_embedding = model.encode(question).tolist()

    # ---------------------------------------------
    # Step 2: Retrieve documents from Pinecone
    # ---------------------------------------------

    index = get_pinecone_index()

    results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True
    )

    # ---------------------------------------------
    # Step 3: Build context from retrieved chunks
    # ---------------------------------------------

    context_chunks = []
    sources = []

    for match in results["matches"]:
        text = match["metadata"]["text"]
        context_chunks.append(text)
        sources.append(text)

    context = "\n".join(context_chunks)

    # ---------------------------------------------
    # Step 4: Build prompt
    # ---------------------------------------------

    prompt = f"""
You are an intelligent AI assistant answering questions using company documents.

Rules:
- Use ONLY the information in the provided context
- Do NOT invent information
- If answer is not present say:
  "The information is not available in the provided documents"

Context:
{context}

User Question:
{question}

Answer:
"""

    # ---------------------------------------------
    # Step 5: Generate answer using Gemini
    # ---------------------------------------------

    response = gemini_model.generate_content(prompt)

    answer = response.text

    return answer, sources