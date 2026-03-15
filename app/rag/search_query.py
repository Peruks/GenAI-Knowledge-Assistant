import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# load env variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "enterprise-rag-index"

# connect to pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# question to search
query = "What is the refund policy?"

# convert question to embedding
query_embedding = model.encode(query).tolist()

# search pinecone
results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True
)

print("\nSearch Results:\n")

for match in results["matches"]:
    print(match["metadata"]["text"])
    print("Score:", match["score"])
    print()