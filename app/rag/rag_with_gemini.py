"""
RAG Pipeline with Pinecone + Gemini

Steps:
1. Convert user question into embedding
2. Retrieve relevant chunks from Pinecone
3. Build context from retrieved chunks
4. Send context + question to Gemini
5. Generate answer with sources
"""

import os
from dotenv import load_dotenv

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

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

model = genai.GenerativeModel("gemini-2.5-flash")


# ------------------------------------------------
# 3. Connect to Pinecone
# ------------------------------------------------

pinecone_index = None

def get_pinecone_index():
    global pinecone_index
    
    if pinecone_index is None:
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index("enterprise-rag-index")
    
    return pinecone_index


# ------------------------------------------------
# 4. Load Embedding Model
# ------------------------------------------------

embedding_model = None

def get_embedding_model():
    global embedding_model
    
    if embedding_model is None:
        print("Loading embedding model...")
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    return embedding_model


# ------------------------------------------------
# 5. User Query
# ------------------------------------------------

query = "What is the refund policy?"


# ------------------------------------------------
# 6. Convert Query to Embedding
# ------------------------------------------------

model = get_embedding_model()

query_embedding = model.encode(query).tolist()


# ------------------------------------------------
# 7. Retrieve Relevant Documents from Pinecone
# ------------------------------------------------

results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True
)


# ------------------------------------------------
# 8. Build Context from Retrieved Chunks
# ------------------------------------------------

context_chunks = []
sources = []

for match in results["matches"]:
    text = match["metadata"]["text"]
    context_chunks.append(text)
    sources.append(text)

context = "\n".join(context_chunks)


# ------------------------------------------------
# 9. Build Prompt for Gemini
# ------------------------------------------------

prompt = f"""
You are an intelligent AI assistant for answering questions using company documents.

Your task is to answer the user's question ONLY using the provided context.

Rules:
- Use only the information from the context.
- Do not invent information.
- If the answer is not present in the context, say:
  "The information is not available in the provided documents."
- Provide a clear and concise answer.
- Mention the relevant source information used.

Context:
{context}

User Question:
{query}

Answer:
"""


# ------------------------------------------------
# 10. Generate Answer using Gemini
# ------------------------------------------------

response = model.generate_content(prompt)

answer = response.text


# ------------------------------------------------
# 11. Display Result
# ------------------------------------------------

print("\n==============================")
print("User Question:")
print(query)

print("\nGenerated Answer:")
print(answer)

print("\nSources Used:")

for s in sources:
    print("-", s)

print("==============================")