# File: tests/test_api.py
# Purpose: Basic API health and route tests
# Connects to: backend/main.py

import requests

BASE_URL = "http://localhost:8000"


def test_health_check():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "PharmIntel API running" in data["message"]
    print("Health check passed:", data["message"])


def test_search_endpoint_exists():
    response = requests.post(
        f"{BASE_URL}/api/v1/search",
        json={"drug_name": "metformin", "max_results": 3},
    )
    # 200 means working, 500 is acceptable in Phase 1 (Supabase not configured yet)
    assert response.status_code in [200, 500]
    print("Search endpoint exists, status:", response.status_code)


if __name__ == "__main__":
    test_health_check()
    test_search_endpoint_exists()
    print("\nAll Phase 1 tests passed.")
