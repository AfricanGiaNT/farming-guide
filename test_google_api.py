#!/usr/bin/env python3
"""
Quick test script for Google Custom Search API credentials
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_search():
    """Test if Google API credentials are working"""
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        print("❌ Missing credentials!")
        print(f"   GOOGLE_API_KEY: {'Set' if api_key else 'Not set'}")
        print(f"   GOOGLE_CSE_ID: {'Set' if cse_id else 'Not set'}")
        return False
    
    # Test search
    query = "agriculture Malawi"
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'num': 1
    }
    
    print(f"🔍 Testing search for: '{query}'")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                print("✅ Google Search API is working!")
                print(f"   Found {len(data['items'])} results")
                print(f"   First result: {data['items'][0]['title']}")
                return True
            else:
                print("⚠️ API working but no results found")
                return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Google Custom Search API Test")
    print("=" * 40)
    
    if test_google_search():
        print("\n✅ Your Google API setup is complete!")
    else:
        print("\n❌ Please check your credentials")
        print("\nTroubleshooting:")
        print("1. Make sure Custom Search API is enabled")
        print("2. Check your API key restrictions")
        print("3. Verify your CSE ID is correct") 