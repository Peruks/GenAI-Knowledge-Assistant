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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

INDEX_NAME = "enterprise-rag-index"


# ------------------------------------------------
# 2. Configure Gemini
# ------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)


# ------------------------------------------------
# 3. Connect to Pinecone
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
# 5. Query to Search
# ------------------------------------------------

query = "What is the refund policy?"


# ------------------------------------------------
# 6. Convert Query to Embedding
# ------------------------------------------------

query_embedding = get_embedding(query)


# ------------------------------------------------
# 7. Search Pinecone
# ------------------------------------------------

results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True
)


# ------------------------------------------------
# 8. Display Results
# ------------------------------------------------

print("\nSearch Results:\n")

for match in results["matches"]:

    text = match["metadata"]["text"]
    score = match["score"]

    print("Result:")
    print(text)
    print("Score:", score)
    print("-" * 40)