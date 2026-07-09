import os
import sys
import requests
import json
from google import genai

def test_gemini():
    print("\n=== Testing Gemini API ===")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        print(" GEMINI_API_KEY is not defined in the environment.")
        return False
        
    print(f"Key loaded: {gemini_key[:8]}...{gemini_key[-4:] if len(gemini_key) > 12 else ''}")
    try:
        client = genai.Client(api_key=gemini_key)
        print("Invoking Gemini (gemini-2.5-flash)...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="Respond with exactly 'Gemini is online and working.'"
        )
        print(f"Status: Success!")
        print(f"Response: {response.text.strip()}")
        return True
    except Exception as e:
        print(f" Gemini Request Failed: {e}")
        return False

def test_openrouter():
    print("\n=== Testing OpenRouter API ===")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")
    
    if not openrouter_key:
        print(" OPENROUTER_API_KEY is not defined in the environment.")
        return False
        
    print(f"Key loaded: {openrouter_key[:8]}...{openrouter_key[-4:] if len(openrouter_key) > 12 else ''}")
    print(f"Target Model: {model}")
    
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Strata Diagnostic Connection Test",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Respond with exactly 'OpenRouter is online and working.'"}]
    }
    
    try:
        print(f"Invoking OpenRouter completions endpoint...")
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result_json = response.json()
            content = result_json["choices"][0]["message"]["content"]
            print(f"Status: Success!")
            print(f"Response: {content.strip()}")
            return True
        else:
            print(f" OpenRouter returned non-200 code.")
            print(f"Response Body: {response.text}")
            return False
    except Exception as e:
        print(f" OpenRouter Request Failed: {e}")
        return False

if __name__ == "__main__":
    # Check if a .env exists locally and load it to assist manual runs
    if os.path.exists(".env"):
        print("Loading environment variables from local .env file...")
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # Fallback manual parsing if dotenv is not installed locally
            with open(".env") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        os.environ[key] = val
                        
    gemini_ok = test_gemini()
    openrouter_ok = test_openrouter()
    
    print("\n=== Diagnostic Summary ===")
    print(f"Gemini API:     {' ONLINE' if gemini_ok else ' OFFLINE/CONFIG ERROR'}")
    print(f"OpenRouter API: {' ONLINE' if openrouter_ok else ' OFFLINE/CONFIG ERROR'}")
    sys.exit(0 if (gemini_ok or openrouter_ok) else 1)
