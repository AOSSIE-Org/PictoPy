"""
Test script for Memories API endpoints.
Run this after starting the backend server.
"""

import requests
import json
from typing import Dict, Any

# Base URL for the API
BASE_URL = "http://localhost:8000"


class MemoriesAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def print_response(self, response: requests.Response, test_name: str):
        """Pretty print API response."""
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
        print(f"{'='*60}\n")

    def test_health_check(self):
        """Test if server is running."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            self.print_response(response, "Health Check")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Server not running: {e}")
            return False

    def test_get_all_images(self):
        """Test getting all images (to verify we have data)."""
        response = self.session.get(f"{self.base_url}/images/")
        self.print_response(response, "Get All Images")
        
        if response.status_code == 200:
            data = response.json()
            image_count = len(data.get("data", []))
            print(f"✅ Found {image_count} images in database")
            return image_count > 0
        return False

    def test_generate_memories(self, force_regenerate: bool = False):
        """Test memory generation."""
        payload = {
            "force_regenerate": force_regenerate
        }
        
        response = self.session.post(
            f"{self.base_url}/memories/generate",
            json=payload
        )
        self.print_response(response, f"Generate Memories (force_regenerate={force_regenerate})")
        
        if response.status_code == 200:
            data = response.json()
            memories_created = data.get("data", {}).get("memories_created", 0)
            stats = data.get("data", {}).get("stats", {})
            
            print(f"✅ Created {memories_created} memories")
            print(f"📊 Stats: {stats}")
            return True
        return False

    def test_get_all_memories(self):
        """Test getting all memories."""
        response = self.session.get(f"{self.base_url}/memories/")
        self.print_response(response, "Get All Memories")
        
        if response.status_code == 200:
            data = response.json()
            memories = data.get("data", [])
            print(f"✅ Retrieved {len(memories)} memories")
            
            # Print memory summaries
            for i, memory in enumerate(memories[:3], 1):  # Show first 3
                print(f"\nMemory {i}:")
                print(f"  Title: {memory['title']}")
                print(f"  Type: {memory['memory_type']}")
                print(f"  Photos: {memory['total_photos']}")
                print(f"  Location: {memory.get('location', 'N/A')}")
            
            return memories
        return []

    def test_get_memory_detail(self, memory_id: str):
        """Test getting a specific memory's details."""
        response = self.session.get(f"{self.base_url}/memories/{memory_id}")
        self.print_response(response, f"Get Memory Detail (ID: {memory_id})")
        
        if response.status_code == 200:
            data = response.json()
            memory = data.get("data", {})
            print(f"✅ Retrieved memory: {memory.get('title')}")
            print(f"   Total images: {len(memory.get('images', []))}")
            return True
        return False

    def test_delete_memory(self, memory_id: str):
        """Test deleting a memory."""
        response = self.session.delete(f"{self.base_url}/memories/{memory_id}")
        self.print_response(response, f"Delete Memory (ID: {memory_id})")
        
        if response.status_code == 200:
            print(f"✅ Memory deleted successfully")
            return True
        return False

    def run_all_tests(self):
        """Run all tests in sequence."""
        print("\n" + "="*60)
        print("STARTING MEMORIES API TESTS")
        print("="*60)

        # Test 1: Health check
        if not self.test_health_check():
            print("❌ Server is not running. Please start the backend server first.")
            return

        # Test 2: Check if we have images
        has_images = self.test_get_all_images()
        if not has_images:
            print("⚠️  Warning: No images found. Upload some images first!")
            print("   Memories require images with date/location metadata.")

        # Test 3: Generate memories
        print("\n🔄 Generating memories...")
        self.test_generate_memories(force_regenerate=True)

        # Test 4: Get all memories
        print("\n📋 Fetching all memories...")
        memories = self.test_get_all_memories()

        # Test 5: Get detail of first memory (if exists)
        if memories:
            first_memory_id = memories[0]["id"]
            print(f"\n🔍 Getting details of first memory...")
            self.test_get_memory_detail(first_memory_id)

            # Test 6: Delete a memory (optional - commented out by default)
            # Uncomment the line below to test deletion
            # self.test_delete_memory(first_memory_id)

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)


def main():
    """Main test function."""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║         PICTOPY MEMORIES API TEST SUITE                ║
    ╚════════════════════════════════════════════════════════╝
    
    This script will test all Memories API endpoints.
    Make sure the backend server is running at http://localhost:8000
    """)

    input("Press Enter to start tests...")

    tester = MemoriesAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()