import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

INDEX_NAME = "enterprise-rag-index"

# configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# connect to Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# user question
query = "What is the refund policy?"

# convert question to embedding
query_embedding = embed_model.encode(query).tolist()

# search Pinecone
results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True
)

# collect retrieved text
context = ""
for match in results["matches"]:
    context += match["metadata"]["text"] + "\n"

# build prompt
prompt = f"""
Use the following information to answer the question.

Context:
{context}

Question:
{query}
"""

# ask Gemini
response = model.generate_content(prompt)

print("\nAnswer:\n")
print(response.text)