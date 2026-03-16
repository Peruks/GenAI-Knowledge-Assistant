"""
Store Embeddings in Pinecone using Gemini Embedding API
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
        model="gemini-embedding-2-preview",
        contents=text
    )

    return result.embeddings[0].values


# ------------------------------------------------
# 5. Load Document
# ------------------------------------------------

with open("data/company_policy.txt", "r", encoding="utf-8") as file:
    text = file.read()


# ------------------------------------------------
# 6. Split Text into Chunks
# ------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

chunks = splitter.split_text(text)


# ------------------------------------------------
# 7. Generate Embeddings
# ------------------------------------------------

vectors = []

for i, chunk in enumerate(chunks):

    embedding = get_embedding(chunk)

    vectors.append({
        "id": f"chunk-{i}",
        "values": embedding,
        "metadata": {"text": chunk}
    })

print(len(get_embedding("test sentence")))
# ------------------------------------------------
# 8. Upload to Pinecone
# ------------------------------------------------

index.upsert(vectors)


print("Embeddings uploaded successfully!")
print(f"Total chunks uploaded: {len(vectors)}")