from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("enterprise-rag-index")

index.delete(delete_all=True)

print("Cleared!")
print("Total vectors:", index.describe_index_stats()["total_vector_count"])