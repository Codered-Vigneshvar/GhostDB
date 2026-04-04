import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Hello! Prove you are online by saying exactly 'Gemini is online and ready for GhostQuery.'")

print(f"API Connection: SUCCESS")
print(f"Response: {response.text}")
