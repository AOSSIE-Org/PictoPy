
import httpx
import json

def test_clusters():
    url = "http://localhost:8000/face-clusters/"
    try:
        response = httpx.get(url)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        clusters = data.get("data", {}).get("clusters", [])
        print(f"Found {len(clusters)} clusters")
        for c in clusters:
            print(f"  - {c.get('cluster_id')}: {c.get('cluster_name')} ({c.get('face_count')} faces)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_clusters()
