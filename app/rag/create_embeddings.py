"""
Create Embeddings using Gemini Embedding API
This script is used to test embedding generation before storing in Pinecone
"""

import os
from dotenv import load_dotenv
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ------------------------------------------------
# 1. Load Environment Variables
# ------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ------------------------------------------------
# 2. Configure Gemini
# ------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)


# ------------------------------------------------
# 3. Gemini Embedding Function
# ------------------------------------------------

def get_embedding(text: str):

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values


# ------------------------------------------------
# 4. Load Document
# ------------------------------------------------

with open("data/company_policy.txt", "r", encoding="utf-8") as file:
    text = file.read()


# ------------------------------------------------
# 5. Split Document into Chunks
# ------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

chunks = splitter.split_text(text)


# ------------------------------------------------
# 6. Generate Embeddings
# ------------------------------------------------

for i, chunk in enumerate(chunks):

    embedding = get_embedding(chunk)

    print(f"\nChunk {i+1}:")
    print(chunk)
    print("Embedding length:", len(embedding))