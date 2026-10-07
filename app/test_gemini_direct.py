from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    raise SystemExit

print("Creating Gemini client...")

client = genai.Client(
    api_key=api_key
)

print("Sending request to Gemini...")

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Reply with exactly: Gemini connection is working."
)

print("\nGemini response:")
print(response.text)