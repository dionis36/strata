import os
import sys
from google import genai
from google.genai import types

def test_api():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    print("Testing gemini-2.5-flash...")
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Say hello world"
        )
        print(f"SUCCESS (gemini-2.5-flash): {res.text.strip()}")
    except Exception as e:
        print(f"FAILED (gemini-2.5-flash): {e}")
        
    print("\nTesting gemini-1.5-flash...")
    try:
        res = client.models.generate_content(
            model='gemini-1.5-flash',
            contents="Say hello world"
        )
        print(f"SUCCESS (gemini-1.5-flash): {res.text.strip()}")
    except Exception as e:
        print(f"FAILED (gemini-1.5-flash): {e}")

if __name__ == "__main__":
    test_api()
