"""
Search Query using Gemini Embeddings + Pinecone
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
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")

INDEX_NAME       = "enterprise-rag-index"
SCORE_THRESHOLD  = 0.3   # minimum relevance score


# ------------------------------------------------
# 2. Configure Gemini Client
# ------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)


# ------------------------------------------------
# 3. Connect to Pinecone
# ------------------------------------------------

pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


# ------------------------------------------------
# 4. Embedding Function
# ------------------------------------------------

def get_embedding(text: str):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ------------------------------------------------
# 5. Search Function
# ------------------------------------------------

def search(query: str, top_k: int = 5):
    """
    Search Pinecone index for relevant chunks.
    Returns only results above SCORE_THRESHOLD.
    """

    print(f"\nQuery: {query}")
    print("-" * 50)

    query_embedding = get_embedding(query)

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    matches = results["matches"]

    if not matches:
        print("No results found.")
        return

    filtered = [m for m in matches if m["score"] > SCORE_THRESHOLD]

    if not filtered:
        print(f"No results above score threshold ({SCORE_THRESHOLD}).")
        print(f"Best score was: {matches[0]['score']:.4f}")
        return

    print(f"Found {len(filtered)} relevant result(s):\n")

    for i, match in enumerate(filtered, 1):
        print(f"Result {i}")
        print(f"Score : {match['score']:.4f}")
        print(f"Source: {match['metadata'].get('source', 'N/A')}")
        print(f"Text  : {match['metadata']['text'][:300]}")
        print("-" * 50)


# ------------------------------------------------
# 6. Run Test Queries
# ------------------------------------------------

if __name__ == "__main__":

    test_queries = [
        "What is the leave policy?",
        "How many sick days do employees get?",
        "What is the password policy?",
        "What is the expense claim process?",
        "What happens during probation period?",
    ]

    for query in test_queries:
        search(query)