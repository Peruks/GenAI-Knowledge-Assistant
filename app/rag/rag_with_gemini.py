"""
RAG Pipeline with Pinecone + Gemini
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai

# ----------------------------------------
# Load Environment Variables
# ----------------------------------------

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

INDEX_NAME = "enterprise-rag-index"

# ----------------------------------------
# Gemini Client
# ----------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)

# ----------------------------------------
# Lazy Pinecone Connection
# ----------------------------------------

pinecone_index = None


def get_pinecone_index():

    global pinecone_index

    if pinecone_index is None:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index(INDEX_NAME)

    return pinecone_index


# ----------------------------------------
# Embedding Function
# ----------------------------------------

def get_embedding(text: str):

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values


# ----------------------------------------
# Retrieve Context
# ----------------------------------------

def retrieve_context(question: str):

    index = get_pinecone_index()

    query_embedding = get_embedding(question)

    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    context_chunks = []
    sources = []

    SCORE_THRESHOLD = 0.55

    if not results.matches:
        return [], []

    for match in results.matches:

        score = match.score

        if score >= SCORE_THRESHOLD:

            text = match.metadata.get("text", "")
            source = match.metadata.get("source", "")
            page = match.metadata.get("page", "")

            if text:
                context_chunks.append(text)

                sources.append({
                    "text": text,
                    "source": source,
                    "page": page
                })

    return context_chunks, sources


# ----------------------------------------
# Main RAG Pipeline
# ----------------------------------------

def ask_rag(question: str):

    context_chunks, sources = retrieve_context(question)

    if not context_chunks:
        return "No relevant information found in the knowledge base.", []

    MAX_CHUNKS = 3
    context = "\n\n".join(context_chunks[:MAX_CHUNKS])

    prompt = f"""
You are an AI assistant answering questions using company documents.

Rules:
- Use ONLY the information from the provided context
- Do NOT invent information
- If the answer is not present say:
  "The information is not available in the provided documents"

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

    answer = response.text if response.text else "No answer generated."

    return answer, sources