#!/usr/bin/env python3
"""
Simple test script for YandexGPT API connection
Run this to test if your API credentials work
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_yandexgpt_api():
    """Test YandexGPT API connection"""
    
    # Get credentials from environment
    api_key = os.getenv('YANDEX_API_KEY')
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    
    print("🧪 Testing YandexGPT API Connection")
    print("=" * 50)
    
    # Check configuration
    print(f"API Key: {'✓ Set' if api_key else '✗ NOT SET'}")
    print(f"Folder ID: {'✓ Set' if folder_id else '✗ NOT SET'}")
    
    if not api_key or not folder_id:
        print("\n❌ Missing configuration!")
        print("Please set YANDEX_API_KEY and YANDEX_FOLDER_ID in your .env file")
        return False
    
    # Test different endpoints
    endpoints = [
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        "https://llm.api.cloud.yandex.net/foundationModels/v1/chat/completions",
        "https://llm.api.cloud.yandex.net/foundationModels/v1/textGeneration"
    ]
    
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    
    test_data = {
        "modelUri": "gpt://b1g8c7pcd9kq2v6u9q3r/yandexgpt-lite",
        "completionOptions": {
            "temperature": "0.1",
            "maxTokens": "50",
            "stream": False
        },
        "messages": [
            {
                "role": "system",
                "text": "You are a helpful assistant."
            },
            {
                "role": "user",
                "text": "Say 'Hello, API test successful!'"
            }
        ]
    }
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n🔍 Testing endpoint {i}: {endpoint}")
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=test_data,
                timeout=30
            )
            
            print(f"  Status: {response.status_code}")
            print(f"  Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"  ✓ Success! Response: {json.dumps(result, indent=2)}")
                    
                    # Try to extract text
                    alternatives = result.get("result", {}).get("alternatives", [])
                    if alternatives and len(alternatives) > 0:
                        message = alternatives[0].get("message", {})
                        text = message.get("text", "")
                        if text:
                            print(f"  📝 Extracted text: {text}")
                            if "API test successful" in text:
                                print("  🎉 API test successful!")
                                return True
                        else:
                            print("  ⚠️ No text content found in response")
                    else:
                        print("  ⚠️ No alternatives found in response")
                        
                except json.JSONDecodeError:
                    print(f"  ⚠️ Response is not valid JSON: {response.text}")
                    
            else:
                print(f"  ❌ Error response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("  ⏰ Request timed out")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request error: {e}")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
    
    print("\n❌ All endpoints failed")
    return False

if __name__ == "__main__":
    success = test_yandexgpt_api()
    if success:
        print("\n✅ YandexGPT API is working!")
    else:
        print("\n❌ YandexGPT API test failed")
        print("\nTroubleshooting tips:")
        print("1. Check your .env file has YANDEX_API_KEY and YANDEX_FOLDER_ID")
        print("2. Verify your API key is correct")
        print("3. Check if your Yandex Cloud account is active")
        print("4. Verify the API endpoint URLs")
