import os
import logging
import requests
from typing import List, Dict, Optional
import time
from urllib.parse import quote

logger = logging.getLogger(__name__)

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"

# Search parameters
MAX_RESULTS = 5
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # seconds

def build_search_query(query: str) -> str:
    """Build an optimized search query for agricultural content"""
    # Add agricultural and location context
    base_terms = ["agriculture", "farming", "crops"]
    location_terms = ["Malawi", "Lilongwe", "Central Region"]
    
    # Check if query already has context
    query_lower = query.lower()
    has_agri_context = any(term in query_lower for term in base_terms)
    has_location_context = any(term in query_lower for term in location_terms)
    
    # Build enhanced query
    enhanced_query = query
    
    if not has_agri_context:
        enhanced_query = f"{query} agriculture farming"
    
    if not has_location_context:
        enhanced_query = f"{enhanced_query} Malawi Lilongwe"
    
    # Add specific agricultural sites for better results
    enhanced_query += " site:agriculture.gov.mw OR site:fao.org OR site:cgiar.org OR site:icrisat.org"
    
    return enhanced_query

def extract_relevant_info(item: Dict) -> Dict[str, str]:
    """Extract relevant information from a search result"""
    return {
        'title': item.get('title', ''),
        'snippet': item.get('snippet', ''),
        'link': item.get('link', ''),
        'source': item.get('displayLink', '')
    }

def search_online(query: str) -> Optional[str]:
    """Search online using Google Custom Search API"""
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        logger.error("Google API credentials not configured")
        return None
    
    # Build optimized query
    search_query = build_search_query(query)
    logger.info(f"Searching for: {search_query}")
    
    # API parameters
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'q': search_query,
        'num': MAX_RESULTS,
        'safe': 'active',
        'fields': 'items(title,snippet,link,displayLink)'
    }
    
    # Retry logic
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = requests.get(
                SEARCH_API_URL, 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                logger.warning(f"No search results found for: {query}")
                # Try a simpler query
                if attempt == 0:
                    params['q'] = f"{query} Malawi agriculture"
                    continue
                return "No information found"
            
            # Process and format results
            results = []
            for item in items[:3]:  # Use top 3 results
                info = extract_relevant_info(item)
                
                # Format each result
                result_text = f"**{info['title']}**\n{info['snippet']}\n"
                
                # Add source attribution
                if info['source']:
                    result_text += f"Source: {info['source']}\n"
                
                results.append(result_text)
            
            # Combine results
            combined_results = "\n---\n".join(results)
            
            # Add search metadata
            search_info = f"Found {len(items)} results for agricultural information about {query} in Malawi.\n\n"
            
            return search_info + combined_results
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                logger.warning("Google API rate limit reached")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return None
            elif e.response.status_code == 403:  # Quota exceeded
                logger.error("Google API quota exceeded")
                return None
            else:
                logger.error(f"HTTP error during search: {e}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during search: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
                continue
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return None
    
    return "No information found"

def search_local_resources(query: str) -> Optional[str]:
    """Search local agricultural resources (fallback when API fails)"""
    # This could be expanded to search local files or databases
    local_resources = {
        "planting season": (
            "Malawi Planting Calendar:\n"
            "• Main season: November-December (with first rains)\n"
            "• Tobacco nurseries: September\n"
            "• Winter crops: May-July (irrigated)\n"
            "• Vegetables: Year-round with irrigation"
        ),
        "soil management": (
            "Soil Management in Lilongwe:\n"
            "• Most soils are sandy loams\n"
            "• Add organic matter (compost/manure)\n"
            "• Practice crop rotation\n"
            "• Use conservation agriculture techniques"
        ),
        "rainfall": (
            "Lilongwe Rainfall Pattern:\n"
            "• Annual average: 800-1000mm\n"
            "• Rainy season: November-April\n"
            "• Peak rainfall: January-February\n"
            "• Dry season: May-October"
        ),
        "extension services": (
            "Agricultural Extension Contacts:\n"
            "• Lilongwe ADD Office: +265 1 754 244\n"
            "• Ministry of Agriculture: +265 1 789 033\n"
            "• LUANAR (Bunda College): +265 1 277 240"
        )
    }
    
    # Simple keyword matching
    query_lower = query.lower()
    for keyword, info in local_resources.items():
        if keyword in query_lower:
            return info
    
    return None

def test_search_api() -> bool:
    """Test if the Google Search API is working"""
    try:
        test_query = "Malawi agriculture"
        result = search_online(test_query)
        return result is not None and result != "No information found"
    except Exception as e:
        logger.error(f"Search API test failed: {e}")
        return False 