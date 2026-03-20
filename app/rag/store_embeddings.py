"""
Store Embeddings in Pinecone using Gemini Embedding API

Pipeline:
Load Documents (TXT + PDF)
    ↓
Clean Text (remove separators)
    ↓
Section-aware Chunking
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
from pypdf import PdfReader


# ------------------------------------------------
# 1. Load Environment Variables
# ------------------------------------------------

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")

INDEX_NAME = "enterprise-rag-index"


# ------------------------------------------------
# 2. Documents to index
# Add any PDF or TXT files here
# ------------------------------------------------

DOCUMENTS = [
    "data/company_policy.txt",
    # "data/ey_code_of_conduct.pdf",
    # "data/ey_sustainability_report.pdf",
    # Add more files here
]


# ------------------------------------------------
# 3. Configure Gemini Client
# ------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)


# ------------------------------------------------
# 4. Connect to Pinecone
# ------------------------------------------------

pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)


# ------------------------------------------------
# 5. Embedding Function
# ------------------------------------------------

def get_embedding(text: str):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


# ------------------------------------------------
# 6. Text Cleaner
# ------------------------------------------------

def clean_text(text: str) -> str:
    """
    Remove separator lines and decorative characters
    that pollute chunks (===, ---, ***, ___, etc.)
    """
    text = re.sub(r'={3,}', ' ', text)      # remove ===...===
    text = re.sub(r'-{3,}', ' ', text)      # remove ---...---
    text = re.sub(r'\*{3,}', ' ', text)     # remove ***...***
    text = re.sub(r'_{3,}', ' ', text)      # remove ___...___
    text = re.sub(r'\|{3,}', ' ', text)     # remove |||...|||
    text = re.sub(r'#{3,}', ' ', text)      # remove ###...###
    text = re.sub(r'\n{3,}', '\n\n', text)  # max 2 blank lines
    text = re.sub(r' {2,}', ' ', text)      # collapse spaces
    text = re.sub(r'\t+', ' ', text)        # replace tabs
    return text.strip()


# ------------------------------------------------
# 7. Section-aware Chunking
# ------------------------------------------------

# Fallback splitter for long sections
_fallback_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=80,
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
)


def split_into_sections(text: str) -> list[str]:
    """
    Split text at natural section boundaries before fixed chunking.
    Detects patterns like:
    - "1. SECTION TITLE"
    - "2.1 Sub-section"
    - "ARTICLE 1 —"
    - "Chapter 1:"
    - Double newline paragraph breaks
    """
    # Pattern covers numbered sections, articles, chapters
    section_pattern = re.compile(
        r'(?=\n(?:'
        r'\d+[\.\d]*\s+[A-Z]'          # 1. TITLE or 1.1 Sub
        r'|[A-Z][A-Z\s]{4,}(?:\n|:)'   # ALL CAPS HEADING
        r'|(?:Article|Chapter|Section|Part)\s+\d+'  # Article 1, Chapter 2
        r'))',
        re.MULTILINE
    )

    raw_sections = section_pattern.split(text)

    chunks = []

    for section in raw_sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= 500:
            # Short enough — keep as one chunk
            if len(section) >= 60:
                chunks.append(section)
        else:
            # Too long — split further at paragraph boundaries
            sub_chunks = _fallback_splitter.split_text(section)
            chunks.extend([c for c in sub_chunks if len(c.strip()) >= 60])

    return chunks


# ------------------------------------------------
# 8. Chunk Validator
# ------------------------------------------------

def is_valid_chunk(text: str) -> bool:
    """
    Filter out low-quality chunks:
    - Too short
    - Mostly dots (TOC lines)
    - Mostly digits
    - No real words
    - Only separator characters
    """
    text = text.strip()

    if len(text) < 60:
        return False

    # Mostly dots (TOC: "Chapter 1 ........... 12")
    dot_ratio = text.count('.') / max(len(text), 1)
    if dot_ratio > 0.25:
        return False

    # Mostly digits
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > 0.4:
        return False

    # No real words (only symbols/numbers)
    if not re.search(r'[a-zA-Z]{3,}', text):
        return False

    # Mostly whitespace
    if len(text.replace(' ', '').replace('\n', '')) < 40:
        return False

    return True


# ------------------------------------------------
# 9. Document Loaders
# ------------------------------------------------

def load_txt(filepath: str) -> str:
    """Load plain text file."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_pdf(filepath: str) -> str:
    """
    Load PDF and extract all text page by page.
    Returns combined text with page markers.
    """
    reader = PdfReader(filepath)
    pages  = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())

    return "\n\n".join(pages)


def load_document(filepath: str) -> str:
    """Auto-detect file type and load."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return load_pdf(filepath)
    elif ext == ".txt":
        return load_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ------------------------------------------------
# 10. Main Indexing Pipeline
# ------------------------------------------------

def index_document(filepath: str) -> int:
    """
    Full pipeline for one document:
    Load → Clean → Section-split → Validate → Embed → Upsert
    Returns number of chunks uploaded.
    """
    filename = os.path.basename(filepath)
    print(f"\n{'='*55}")
    print(f"Processing: {filename}")
    print(f"{'='*55}")

    # Load
    raw_text = load_document(filepath)
    print(f"Loaded — {len(raw_text):,} characters")

    # Clean
    text = clean_text(raw_text)
    print(f"Cleaned — {len(text):,} characters")

    # Section-aware split
    raw_chunks = split_into_sections(text)
    print(f"Raw chunks from section split: {len(raw_chunks)}")

    # Validate
    chunks = [c for c in raw_chunks if is_valid_chunk(c)]
    print(f"Valid chunks after filtering: {len(chunks)}")
    print(f"Skipped: {len(raw_chunks) - len(chunks)} junk chunks")

    if not chunks:
        print(f"WARNING: No valid chunks from {filename}. Skipping.")
        return 0

    # Embed + upsert
    vectors  = []
    uploaded = 0

    print(f"\nEmbedding and uploading...")

    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk)

            vectors.append({
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": {
                    "text":        chunk,
                    "source":      filename,
                    "filepath":    filepath,
                    "chunk_index": i,
                    "chunk_total": len(chunks)
                }
            })

            # Batch upsert every 25
            if len(vectors) >= 25:
                index.upsert(vectors)
                uploaded += len(vectors)
                print(f"  Uploaded {uploaded}/{len(chunks)} chunks...")
                vectors = []
                gc.collect()

        except Exception as e:
            print(f"  Error on chunk {i}: {e}")
            continue

    # Remaining
    if vectors:
        index.upsert(vectors)
        uploaded += len(vectors)
        gc.collect()

    print(f"Done: {uploaded} chunks from {filename}")
    return uploaded


# ------------------------------------------------
# 11. Run All Documents
# ------------------------------------------------

if __name__ == "__main__":

    print("\nNEXUS — Embedding Pipeline")
    print(f"Index: {INDEX_NAME}")
    print(f"Documents to process: {len(DOCUMENTS)}")

    # Check which files exist
    valid_docs = []
    for path in DOCUMENTS:
        if os.path.exists(path):
            valid_docs.append(path)
        else:
            print(f"WARNING: File not found — {path} (skipping)")

    if not valid_docs:
        print("No valid documents found. Exiting.")
        exit(1)

    # Index each document
    total_uploaded = 0
    results        = {}

    for doc_path in valid_docs:
        try:
            count = index_document(doc_path)
            results[doc_path] = count
            total_uploaded += count
        except Exception as e:
            print(f"ERROR processing {doc_path}: {e}")
            results[doc_path] = 0

    # Summary
    print(f"\n{'='*55}")
    print("INDEXING COMPLETE")
    print(f"{'='*55}")

    for path, count in results.items():
        name = os.path.basename(path)
        print(f"  {name:<40} {count:>4} chunks")

    print(f"{'─'*55}")
    print(f"  {'TOTAL':<40} {total_uploaded:>4} chunks")

    # Verify in Pinecone
    stats = index.describe_index_stats()
    print(f"\nPinecone index total vectors: {stats['total_vector_count']}")