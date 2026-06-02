import os
import requests
import json

openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
model = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")

print(f"Key loaded: {bool(openrouter_key)}")
print(f"Model: {model}")

headers = {
    "Authorization": f"Bearer {openrouter_key}",
    "HTTP-Referer": "http://localhost:8000",
    "X-Title": "Strata Advisory Suite",
    "Content-Type": "application/json"
}

data = {
    "model": model,
    "messages": [{"role": "user", "content": "Hello, return a simple JSON object {\"test\": \"success\"}"}],
    "response_format": {"type": "json_object"}
}

try:
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
