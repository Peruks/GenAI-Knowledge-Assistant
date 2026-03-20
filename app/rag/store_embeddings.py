"""
Store Embeddings in Pinecone using Gemini Embedding API

Pipeline:
Load Document
    ↓
Clean Text (remove separators)
    ↓
Split into Chunks
    ↓
Validate Chunks
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
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ------------------------------------------------
# 5. Text Cleaner — remove separators and junk
# ------------------------------------------------

def clean_text(text: str) -> str:
    """
    Remove separator lines, excess whitespace and decorative characters
    that pollute chunks (===, ---, ***, ___, etc.)
    """
    text = re.sub(r'={3,}', ' ', text)     # remove ===...===
    text = re.sub(r'-{3,}', ' ', text)     # remove ---...---
    text = re.sub(r'\*{3,}', ' ', text)    # remove ***...***
    text = re.sub(r'_{3,}', ' ', text)     # remove ___...___
    text = re.sub(r'\n{3,}', '\n\n', text) # max 2 blank lines
    text = re.sub(r' {2,}', ' ', text)     # collapse multiple spaces
    return text.strip()


# ------------------------------------------------
# 6. Chunk Validator — skip TOC, dots, junk
# ------------------------------------------------

def is_valid_chunk(text: str) -> bool:
    """
    Filter out low-quality chunks:
    - Too short
    - Mostly dots (TOC lines)
    - Mostly digits
    - No real words
    """
    text = text.strip()

    if len(text) < 60:
        return False

    dot_ratio = text.count('.') / max(len(text), 1)
    if dot_ratio > 0.25:
        return False

    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > 0.4:
        return False

    if not re.search(r'[a-zA-Z]{3,}', text):
        return False

    return True


# ------------------------------------------------
# 7. Load Document
# ------------------------------------------------

DOC_PATH = "data/company_policy.txt"

print(f"Loading document: {DOC_PATH}")

with open(DOC_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Clean before splitting
text = clean_text(text)

print(f"Document loaded — {len(text)} characters")


# ------------------------------------------------
# 8. Split into Chunks
# ------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

raw_chunks = splitter.split_text(text)

print(f"Raw chunks: {len(raw_chunks)}")

chunks = [c for c in raw_chunks if is_valid_chunk(c)]

print(f"Valid chunks after filtering: {len(chunks)}")
print(f"Skipped: {len(raw_chunks) - len(chunks)} junk chunks")


# ------------------------------------------------
# 9. Generate Embeddings and Upsert
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
                "text":        chunk,
                "source":      DOC_PATH,
                "chunk_index": i
            }
        })

        if len(vectors) >= 25:
            index.upsert(vectors)
            uploaded += len(vectors)
            print(f"  Uploaded {uploaded}/{len(chunks)} chunks...")
            vectors = []
            gc.collect()

    except Exception as e:
        print(f"  Error on chunk {i}: {e}")
        continue

if vectors:
    index.upsert(vectors)
    uploaded += len(vectors)
    gc.collect()

print(f"\nDone!")
print(f"Total chunks uploaded: {uploaded}")
print(f"Index: {INDEX_NAME}")


# ------------------------------------------------
# 10. Verify Upload
# ------------------------------------------------

stats = index.describe_index_stats()
print(f"Total vectors in index: {stats['total_vector_count']}")