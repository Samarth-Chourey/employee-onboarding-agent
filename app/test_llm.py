import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0
)

response = llm.invoke(
    "Explain employee onboarding in one simple sentence."
)

print(response.content)