"""
Query available models from Gemini and Anthropic APIs.
Run with: python scripts/list_available_models.py
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("AVAILABLE MODELS QUERY")
print("=" * 60)

# =============================================================================
# GEMINI MODELS
# =============================================================================
print("\n📦 GEMINI MODELS")
print("-" * 40)

google_key = os.getenv("GOOGLE_API_KEY")
if not google_key:
    print("❌ GOOGLE_API_KEY not set")
else:
    print(f"✅ GOOGLE_API_KEY found (ends with ...{google_key[-4:]})")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=google_key)
        
        print("\nAvailable Gemini models:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  • {model.name}")
    except ImportError:
        print("⚠️ google-generativeai not installed, trying langchain...")
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Try a few known model names
            test_models = [
                "gemini-pro",
                "gemini-1.0-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ]
            
            print("\nTesting model availability:")
            for model_name in test_models:
                try:
                    llm = ChatGoogleGenerativeAI(
                        model=model_name, 
                        google_api_key=google_key,
                    )
                    result = llm.invoke("Hi")
                    print(f"  ✅ {model_name} - WORKS")
                except Exception as e:
                    error_msg = str(e)[:50]
                    print(f"  ❌ {model_name} - {error_msg}")
        except ImportError:
            print("❌ langchain_google_genai not installed")
    except Exception as e:
        print(f"❌ Error: {e}")

# =============================================================================
# ANTHROPIC MODELS
# =============================================================================
print("\n\n📦 ANTHROPIC MODELS")
print("-" * 40)

anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_key:
    print("❌ ANTHROPIC_API_KEY not set")
else:
    print(f"✅ ANTHROPIC_API_KEY found (ends with ...{anthropic_key[-4:]})")
    
    try:
        from langchain_anthropic import ChatAnthropic
        
        # Known Claude models
        test_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-opus-20240229",
        ]
        
        print("\nTesting model availability:")
        for model_name in test_models:
            try:
                llm = ChatAnthropic(
                    model=model_name,
                    anthropic_api_key=anthropic_key,
                )
                result = llm.invoke("Hi")
                print(f"  ✅ {model_name} - WORKS")
            except Exception as e:
                error_msg = str(e)[:60]
                print(f"  ❌ {model_name} - {error_msg}")
    except ImportError:
        print("❌ langchain_anthropic not installed")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
