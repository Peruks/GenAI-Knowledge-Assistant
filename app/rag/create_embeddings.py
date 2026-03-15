from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load document
with open("data/company_policy.txt", "r", encoding="utf-8") as file:
    text = file.read()

# Split text
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

chunks = splitter.split_text(text)

# Create embeddings
for i, chunk in enumerate(chunks):
    embedding = model.encode(chunk)

    print(f"\nChunk {i+1}:")
    print(chunk)
    print("Embedding length:", len(embedding))