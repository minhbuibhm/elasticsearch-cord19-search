"""
TEST SUITE - SEARCH ENGINE
--------------------------
Purpose:
    Verifies that the backend API and Elasticsearch integration are working.
    Tests all 3 search modes + analytics.

Usage:
    Run this script directly:
    python test_search.py
"""

from fastapi.testclient import TestClient
from main import app
from pprint import pprint
import time

# Initialize the Test Client
# This wraps the FastAPI app so we can send requests to it directly in Python
client = TestClient(app)

def print_separator(title):
    print("\n" + "=" * 60)
    print(f" {title.upper()}")
    print("=" * 60)

def test_endpoint(endpoint: str, query: str, year: str = None):
    """Generic helper to test any search endpoint"""
    print(f"\n>>> Testing {endpoint} with query='{query}'" + (f" & year='{year}'" if year else ""))
    
    start_time = time.time()
    
    # Construct params
    params = {"search_query": query, "limit": 3}
    if year:
        params["year"] = year

    # Send Request
    response = client.get(endpoint, params=params)
    
    # Calculate Latency
    latency = (time.time() - start_time) * 1000

    # 1. Check Status Code
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        print(response.text)
        return

    data = response.json()
    hits = data.get("hits", [])
    total = data.get("total", 0)

    # 2. Print Summary
    print(f"✅ SUCCESS ({latency:.2f}ms)")
    print(f"   Total Hits Found: {total}")
    print(f"   Returned: {len(hits)}")

    # 3. Return the first ID found so we can test the 'details' endpoint later
    if hits:
        first_hit = hits[0]
        return first_hit.get("_id")
    return None

def test_analytics(query: str):
    """Tests the timeline aggregation endpoint"""
    endpoint = "/api/v1/get_docs_per_year_count/"
    print(f"\n>>> Testing {endpoint} with query='{query}'")
    
    response = client.get(endpoint, params={"search_query": query})
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        return

    data = response.json()
    docs_per_year = data.get("docs_per_year", {})
    
    print("✅ SUCCESS")
    print("   Timeline Data Sample:")
    # Print first 5 years found
    for year, count in list(docs_per_year.items())[:5]:
        print(f"   {year}: {count} papers")

def test_paper_details(doc_id: str):
    """Tests the Paper Details + Related Papers endpoint"""
    endpoint = "/api/v1/get_paper_details/"
    print(f"\n>>> Testing {endpoint} with doc_id='{doc_id}'")

    response = client.get(endpoint, params={"doc_id": doc_id})

    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    details = data.get("paper_details", {})
    related = data.get("related_papers", [])

    print("✅ SUCCESS")
    print(f"   Title: {details.get('title')[:60]}...")
    print(f"   Related Papers Found: {len(related)}")
    
    if related:
        print("   --- Top Related Paper ---")
        print(f"   Title: {related[0]['_source'].get('title')[:60]}...")


def run_all_tests():
    print("Starting System Tests...")
    
    # TEST 1: Regular BM25 Search
    print_separator("1. Lexical Search (BM25)")
    # Capture an ID to test details later
    sample_doc_id = test_endpoint("/api/v1/regular_search/", query="corona")

    # TEST 2: Semantic Vector Search
    print_separator("2. Semantic Search (SciBERT)")
    test_endpoint("/api/v1/semantic_search/", query="mental health issues")

    # TEST 3: Hybrid Search (RRF)
    print_separator("3. Hybrid Search (RRF)")
    test_endpoint("/api/v1/hybrid_search/", query="depression treatment")

    # TEST 4: Filters
    print_separator("4. Filter Test (Year 2021)")
    test_endpoint("/api/v1/hybrid_search/", query="depression", year="2021")

    # TEST 5: Analytics
    print_separator("5. Analytics")
    test_analytics(query="depression")

    # TEST 6: Paper Details & Recommendations
    if sample_doc_id:
        print_separator("6. Paper Details & Related (Recommendations)")
        test_paper_details(sample_doc_id)
    else:
        print("\n⚠️ Skipping Test 6 because no documents were found in Test 1.")

if __name__ == "__main__":
    # Ensure model is loaded before running tests
    print("Initializing Test Client (Loading Model may take a moment)...")
    try:
        run_all_tests()
        print("\nAll tests completed.")
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        print("Tip: Make sure Elasticsearch is running and index_data.py has been executed.")