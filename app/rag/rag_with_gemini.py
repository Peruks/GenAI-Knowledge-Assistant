"""
RAG Pipeline with Pinecone + Gemini

Pipeline Steps
1. Convert question → embedding
2. Retrieve relevant chunks from Pinecone
3. Filter by similarity score
4. Build context
5. Send context + question to Gemini
6. Return answer + sources
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai

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
# 3. Lazy Pinecone Connection
# ------------------------------------------------

pinecone_index = None


def get_pinecone_index():
    """
    Lazy load Pinecone index.
    Prevents connection during API startup.
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

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values


# ------------------------------------------------
# 5. Retrieve Context
# ------------------------------------------------

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

    for match in results.matches:

        score = match.score

        if score >= SCORE_THRESHOLD:

            text = match.metadata.get("text", "")

            if text:
                context_chunks.append(text)
                sources.append(text)

    return context_chunks, sources


# ------------------------------------------------
# 6. Main RAG Pipeline
# ------------------------------------------------

def ask_rag(question: str):
    """
    End-to-end RAG pipeline
    """

    context_chunks, sources = retrieve_context(question)

    # If nothing relevant found
    if not context_chunks:
        return "No relevant information found in the knowledge base.", []

    # Limit context size
    MAX_CHUNKS = 3
    context_chunks = context_chunks[:MAX_CHUNKS]

    context = "\n\n".join(context_chunks)

    # ------------------------------------------------
    # Prompt
    # ------------------------------------------------

    prompt = f"""
You are an AI assistant answering questions using company documents.

Rules:
- Use ONLY the information from the provided context
- Do NOT invent information
- If answer is not present say:
  "The information is not available in the provided documents"

Context:
{context}

User Question:
{question}

Answer:
"""

    # ------------------------------------------------
    # Generate Answer
    # ------------------------------------------------

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    answer = response.text

    return answer, sources