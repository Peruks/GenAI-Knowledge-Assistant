import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

with open("models.txt", "w") as f:
    f.write("Listing available models...\n")
    try:
        models = client.models.list()
        for m in models:
            f.write(f"Model ID: {m.name}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
