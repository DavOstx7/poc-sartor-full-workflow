"""
Direct API test without LangChain wrapper.
Run with: python scripts/test_api_direct.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("DIRECT API TEST")
print("=" * 60)

# =============================================================================
# Test Anthropic directly
# =============================================================================
print("\n📦 ANTHROPIC DIRECT TEST")
print("-" * 40)

anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    print(f"Key length: {len(anthropic_key)}")
    print(f"Key prefix: {anthropic_key[:10]}...")
    print(f"Key suffix: ...{anthropic_key[-4:]}")
    
    # Direct API call
    headers = {
        "x-api-key": anthropic_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Say hi"}]
    }
    
    print("\nMaking direct API call to Anthropic...")
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("❌ ANTHROPIC_API_KEY not set")

# =============================================================================
# Test Gemini directly  
# =============================================================================
print("\n\n📦 GEMINI DIRECT TEST")
print("-" * 40)

google_key = os.getenv("GOOGLE_API_KEY")
if google_key:
    print(f"Key length: {len(google_key)}")
    print(f"Key prefix: {google_key[:10]}...")
    print(f"Key suffix: ...{google_key[-4:]}")
    
    # Direct API call to list models
    url = f"https://generativelanguage.googleapis.com/v1/models?key={google_key}"
    
    print("\nListing available models from Gemini API...")
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"\nFound {len(models)} models:")
            for m in models[:15]:  # First 15
                name = m.get("name", "")
                print(f"  • {name}")
            if len(models) > 15:
                print(f"  ... and {len(models) - 15} more")
        else:
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("❌ GOOGLE_API_KEY not set")

print("\n" + "=" * 60)
