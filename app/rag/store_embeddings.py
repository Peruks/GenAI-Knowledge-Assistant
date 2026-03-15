import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# load .env variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "enterprise-rag-index"

# connect to Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# read document
with open("data/company_policy.txt", "r", encoding="utf-8") as file:
    text = file.read()

# split text
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

chunks = splitter.split_text(text)

vectors = []

for i, chunk in enumerate(chunks):
    embedding = model.encode(chunk).tolist()

    vectors.append({
        "id": f"chunk-{i}",
        "values": embedding,
        "metadata": {"text": chunk}
    })

# upload to pinecone
index.upsert(vectors)

print("Embeddings uploaded to Pinecone!")