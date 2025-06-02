#!/usr/bin/env python3
"""
Test script for the Agricultural Advisor Bot
Run this to test individual components before full deployment
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment():
    """Test if all required environment variables are set"""
    print("\n🔍 Testing Environment Variables...")
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "OPENAI_API_KEY", 
        "GOOGLE_API_KEY",
        "GOOGLE_CSE_ID",
        "DATABASE_URL"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set (length: {len(value)})")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    return all_set

def test_database():
    """Test database connection and initialization"""
    print("\n🔍 Testing Database Connection...")
    try:
        from database import init_db, search_db, get_popular_queries
        
        # Initialize database
        init_db()
        print("✅ Database initialized successfully")
        
        # Test search
        test_query = "What crops grow best in Lilongwe?"
        result = search_db(test_query)
        if result:
            print(f"✅ Database search working - Found result for: {test_query}")
        else:
            print("⚠️ No results found in database (this is normal for empty database)")
        
        # Get popular queries
        popular = get_popular_queries(5)
        print(f"✅ Popular queries function working - Found {len(popular)} entries")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_search_api():
    """Test Google Custom Search API"""
    print("\n🔍 Testing Google Search API...")
    try:
        from search import test_search_api, search_online
        
        if test_search_api():
            print("✅ Google Search API is working")
            
            # Try a sample search
            result = search_online("maize farming Malawi")
            if result and result != "No information found":
                print("✅ Sample search successful")
                print(f"   Preview: {result[:100]}...")
            else:
                print("⚠️ Search returned no results")
        else:
            print("❌ Google Search API test failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Search API error: {e}")
        return False

def test_openai():
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI API...")
    try:
        import openai
        from ai_agent import generate_response
        
        # Test with a simple prompt
        test_prompt = "Say 'Hello, I am working!' if you can read this."
        response = generate_response(test_prompt, temperature=0)
        
        if response and "working" in response.lower():
            print("✅ OpenAI API is working")
            print(f"   Response: {response}")
            return True
        else:
            print("❌ OpenAI API test failed")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

def test_telegram_bot():
    """Test Telegram bot token validity"""
    print("\n🔍 Testing Telegram Bot Token...")
    try:
        import requests
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("❌ Telegram bot token not set")
            return False
            
        # Test token by getting bot info
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"✅ Telegram bot token is valid")
                print(f"   Bot name: @{bot_info.get('username', 'unknown')}")
                print(f"   Bot ID: {bot_info.get('id', 'unknown')}")
                return True
        
        print("❌ Invalid Telegram bot token")
        return False
        
    except Exception as e:
        print(f"❌ Telegram API error: {e}")
        return False

def test_query_processing():
    """Test the complete query processing pipeline"""
    print("\n🔍 Testing Query Processing Pipeline...")
    try:
        from ai_agent import process_query
        
        test_queries = [
            "What crops grow best in Lilongwe?",
            "When should I plant maize?",
            "How to control pests?"
        ]
        
        for query in test_queries:
            print(f"\n   Testing: '{query}'")
            response = process_query(query)
            
            if response and len(response) > 10:
                print(f"   ✅ Got response (length: {len(response)} chars)")
                print(f"   Preview: {response[:150]}...")
            else:
                print(f"   ❌ No valid response")
                
        return True
        
    except Exception as e:
        print(f"❌ Query processing error: {e}")
        return False

def main():
    """Run all tests"""
    print("🌾 Agricultural Advisor Bot - System Test 🌾")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Database Connection", test_database),
        ("Telegram Bot Token", test_telegram_bot),
        ("Google Search API", test_search_api),
        ("OpenAI API", test_openai),
        ("Query Processing", test_query_processing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The bot is ready to run.")
        print("Run 'python main.py' to start the bot.")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration above.")
        print("Make sure all API keys and tokens are correctly set in your .env file.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)