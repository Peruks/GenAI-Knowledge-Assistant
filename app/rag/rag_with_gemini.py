"""
RAG Pipeline with Pinecone + Gemini

Pipeline Steps:
1. Convert user question into embedding (Gemini)
2. Retrieve relevant chunks from Pinecone
3. Build context from retrieved chunks
4. Send context + question to Gemini
5. Generate answer with sources
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
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
    Prevents initialization during server startup.
    """

    global pinecone_index

    if pinecone_index is None:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index(INDEX_NAME)

    return pinecone_index


# ------------------------------------------------
# 4. Gemini Embedding Function
# ------------------------------------------------

def get_embedding(text: str):
    """
    Generate embeddings using Gemini API
    """

    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_query"
    )

    return result["embedding"]


# ------------------------------------------------
# 5. Main RAG Pipeline Function
# ------------------------------------------------

def ask_rag(question: str):
    """
    Improved RAG pipeline with relevance filtering
    """

    # ---------------------------------------------
    # Step 1: Convert question to embedding
    # ---------------------------------------------

    query_embedding = get_embedding(question)

    # ---------------------------------------------
    # Step 2: Retrieve documents from Pinecone
    # ---------------------------------------------

    index = get_pinecone_index()

    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    # ---------------------------------------------
    # Step 3: Filter by relevance score
    # ---------------------------------------------

    context_chunks = []
    sources = []

    SCORE_THRESHOLD = 0.55

    for match in results["matches"]:

        score = match["score"]

        if score >= SCORE_THRESHOLD:

            text = match["metadata"]["text"]

            context_chunks.append(text)
            sources.append(text)

    # If nothing relevant found
    if not context_chunks:
        return "No relevant information found in the knowledge base.", []

    # ---------------------------------------------
    # Step 4: Limit context size
    # ---------------------------------------------

    MAX_CHUNKS = 3
    context_chunks = context_chunks[:MAX_CHUNKS]

    context = "\n".join(context_chunks)

    # ---------------------------------------------
    # Step 5: Prompt
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
    # Step 6: Generate answer
    # ---------------------------------------------

    response = gemini_model.generate_content(prompt)

    answer = response.text

    return answer, sources