# test_cohere.py - UPDATED WITH CURRENT MODELS
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

api_key = os.environ.get('COHERE_API_KEY')

if not api_key:
    print("❌ No API key found in .env file")
    print("Add: COHERE_API_KEY=your_key_here")
    exit(1)

print(f"Testing Cohere API key: {api_key[:10]}...")

# Test 1: Get available models
try:
    response = requests.get(
        'https://api.cohere.com/v1/models',
        headers={'Authorization': f'Bearer {api_key}'},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        models = result.get('models', [])
        print("✅ Cohere API key is valid")
        print(f"Available models ({len(models)} total):")
        
        # Show all available models
        for model in models:
            print(f"  - {model}")
        
        # Check for recommended chat models
        chat_models = []
        for model in models:
            if any(keyword in model.lower() for keyword in ['command-r', 'aya', 'c4ai']):
                chat_models.append(model)
        
        if chat_models:
            print(f"\nRecommended chat models: {', '.join(chat_models[:10])}")
        else:
            print("\nNo specific chat models found. Trying all models...")
            
    else:
        print(f"❌ Cohere API key test failed: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error testing Cohere API: {e}")

# Test 2: Try available models for chat
print("\n" + "="*60)
print("Testing available models for Chat API...")
print("="*60)

# Models to try (based on Cohere's current offerings)
models_to_test = [
    'command-r-08-2024',  # Latest Command R
    'command-r-plus-08-2024',  # Latest Command R Plus
    'command-r',  # General Command R
    'command-r-plus',  # General Command R Plus
    'aya-23-8B',  # Aya model
    'aya-23-35B',  # Larger Aya model
    'c4ai-command-r-v01',  # C4AI model
    'c4ai-command-r-plus',  # C4AI plus model
]

successful_models = []

for model_name in models_to_test:
    try:
        print(f"\nTrying model: {model_name}")
        
        response = requests.post(
            'https://api.cohere.com/v1/chat',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model_name,
                'message': 'Hello, how are you?',
                'temperature': 0.1,
                'max_tokens': 50
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '').strip()
            print(f"✅ SUCCESS: {model_name}")
            print(f"   Response: {text[:80]}...")
            successful_models.append(model_name)
        elif response.status_code == 404:
            print(f"❌ Model not found: {model_name}")
        elif response.status_code == 400:
            print(f"⚠️ Model not suitable for chat: {model_name}")
        else:
            print(f"❌ Failed ({response.status_code}): {model_name}")
            
    except Exception as e:
        print(f"❌ Error with {model_name}: {e}")

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
if successful_models:
    print(f"✅ Working models: {', '.join(successful_models)}")
    print(f"\n🎯 RECOMMENDED: Use '{successful_models[0]}' in your app")
else:
    print("❌ No working models found. Check your API key permissions.")
    print("\nPossible issues:")
    print("1. Your API key might not have access to chat models")
    print("2. Check billing/usage limits at https://dashboard.cohere.com")
    print("3. Try creating a new API key")