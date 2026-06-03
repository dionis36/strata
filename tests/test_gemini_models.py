import os
import sys
from google import genai

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    for m in client.models.list():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

if __name__ == "__main__":
    list_models()
