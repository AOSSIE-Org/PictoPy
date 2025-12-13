"""
Test script for Memories API endpoints

This script tests all the Memories feature endpoints to verify they're working correctly.

Usage:
    python test_memories_api.py
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/memories"


def print_response(endpoint: str, response: requests.Response):
    """Pretty print API response."""
    print("\n" + "="*70)
    print(f"🔍 Testing: {endpoint}")
    print("="*70)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS")
        data = response.json()
        print("\nResponse Preview:")
        print(json.dumps(data, indent=2)[:500] + "...")
    else:
        print("❌ FAILED")
        print(f"Error: {response.text}")
    print("="*70)


def test_generate_memories():
    """Test POST /api/memories/generate"""
    print("\n🚀 Testing: Generate Memories")
    
    response = requests.post(
        f"{BASE_URL}/generate",
        params={
            "location_radius_km": 5.0,
            "date_tolerance_days": 3,
            "min_images": 2
        }
    )
    
    print_response("POST /api/memories/generate", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Summary:")
        print(f"   - Memory Count: {data.get('memory_count', 0)}")
        print(f"   - Image Count: {data.get('image_count', 0)}")
        print(f"   - Message: {data.get('message', 'N/A')}")


def test_timeline():
    """Test GET /api/memories/timeline"""
    print("\n🚀 Testing: Timeline")
    
    response = requests.get(
        f"{BASE_URL}/timeline",
        params={
            "days": 30,
            "location_radius_km": 5.0,
            "date_tolerance_days": 3
        }
    )
    
    print_response("GET /api/memories/timeline", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Summary:")
        print(f"   - Memory Count: {data.get('memory_count', 0)}")
        print(f"   - Date Range: {data.get('date_range', {})}")


def test_on_this_day():
    """Test GET /api/memories/on-this-day"""
    print("\n🚀 Testing: On This Day")
    
    response = requests.get(f"{BASE_URL}/on-this-day")
    
    print_response("GET /api/memories/on-this-day", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Summary:")
        print(f"   - Today: {data.get('today', 'N/A')}")
        print(f"   - Years Found: {data.get('years', [])}")
        print(f"   - Image Count: {data.get('image_count', 0)}")


def test_locations():
    """Test GET /api/memories/locations"""
    print("\n🚀 Testing: Locations")
    
    response = requests.get(
        f"{BASE_URL}/locations",
        params={
            "location_radius_km": 5.0,
            "max_sample_images": 3
        }
    )
    
    print_response("GET /api/memories/locations", response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Summary:")
        print(f"   - Location Count: {data.get('location_count', 0)}")
        if data.get('locations'):
            print(f"   - Top Location: {data['locations'][0].get('location_name', 'N/A')}")
            print(f"   - Photos at Top Location: {data['locations'][0].get('image_count', 0)}")


def check_server():
    """Check if the server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print("⚠️ Server responded but with unexpected status")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running!")
        print("\n💡 Start the server with:")
        print("   cd /Users/harshit/Code/pictopy/PictoPy/backend")
        print("   python main.py")
        return False


def main():
    """Run all tests."""
    print("\n" + "🎯 " * 20)
    print("      MEMORIES API TEST SUITE")
    print("🎯 " * 20 + "\n")
    
    # Check if server is running
    if not check_server():
        return
    
    print("\n⏳ Running all tests...\n")
    
    try:
        # Run all tests
        test_generate_memories()
        test_timeline()
        test_on_this_day()
        test_locations()
        
        print("\n" + "✅ " * 20)
        print("      ALL TESTS COMPLETED!")
        print("✅ " * 20 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
