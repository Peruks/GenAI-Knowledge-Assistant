"""
Store Embeddings in Pinecone using Gemini Embedding API

Pipeline:
Load Document
    ↓
Clean + Validate Chunks
    ↓
Generate Gemini Embeddings
    ↓
Upsert to Pinecone
"""

import os
import re
import gc
import uuid
from dotenv import load_dotenv
from pinecone import Pinecone
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ------------------------------------------------
# 1. Load Environment Variables
# ------------------------------------------------

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")

INDEX_NAME = "enterprise-rag-index"


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
        model="gemini-embedding-001",   # 3072 dims — matches your index
        contents=text
    )
    return result.embeddings[0].values


# ------------------------------------------------
# 5. Chunk Validation — skip TOC, dots, junk
# ------------------------------------------------

def is_valid_chunk(text: str) -> bool:
    """
    Filter out low-quality chunks like:
    - Table of contents lines (dotted lines + page numbers)
    - Very short chunks
    - Chunks that are mostly numbers or dots
    """
    text = text.strip()

    # Too short
    if len(text) < 60:
        return False

    # Mostly dots (TOC lines like "Chapter 1 ........... 12")
    dot_ratio = text.count('.') / max(len(text), 1)
    if dot_ratio > 0.25:
        return False

    # Mostly digits
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > 0.4:
        return False

    # Only whitespace or symbols
    if not re.search(r'[a-zA-Z]{3,}', text):
        return False

    return True


# ------------------------------------------------
# 6. Load Document
# ------------------------------------------------

DOC_PATH = "data/company_policy.txt"

print(f"Loading document: {DOC_PATH}")

with open(DOC_PATH, "r", encoding="utf-8") as f:
    text = f.read()

print(f"Document loaded — {len(text)} characters")


# ------------------------------------------------
# 7. Split into Chunks
# ------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # increased from 200 — better semantic chunks
    chunk_overlap=100    # increased from 50 — better context continuity
)

raw_chunks = splitter.split_text(text)

print(f"Raw chunks: {len(raw_chunks)}")

# Filter out junk chunks
chunks = [c for c in raw_chunks if is_valid_chunk(c)]

print(f"Valid chunks after filtering: {len(chunks)}")
print(f"Skipped: {len(raw_chunks) - len(chunks)} junk chunks")


# ------------------------------------------------
# 8. Generate Embeddings and Upsert
# ------------------------------------------------

vectors  = []
uploaded = 0

print("\nGenerating embeddings and uploading to Pinecone...")

for i, chunk in enumerate(chunks):

    try:
        embedding = get_embedding(chunk)

        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                "text": chunk,
                "source": DOC_PATH,
                "chunk_index": i
            }
        })

        # Batch upsert every 25 vectors
        if len(vectors) >= 25:
            index.upsert(vectors)
            uploaded += len(vectors)
            print(f"  Uploaded {uploaded}/{len(chunks)} chunks...")
            vectors = []
            gc.collect()

    except Exception as e:
        print(f"  Error on chunk {i}: {e}")
        continue

# Upload remaining
if vectors:
    index.upsert(vectors)
    uploaded += len(vectors)
    gc.collect()

print(f"\nDone!")
print(f"Total chunks uploaded: {uploaded}")
print(f"Index: {INDEX_NAME}")


# ------------------------------------------------
# 9. Verify Upload
# ------------------------------------------------

stats = index.describe_index_stats()
print(f"Total vectors in index: {stats['total_vector_count']}")