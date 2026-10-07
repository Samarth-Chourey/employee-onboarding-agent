from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found")
    raise SystemExit

client = genai.Client(api_key=api_key)

print("\n========== AVAILABLE MODELS ==========\n")

for model in client.models.list():
    print(model.name)

print("\n======================================")