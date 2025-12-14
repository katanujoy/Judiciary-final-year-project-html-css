# test_api.py
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_endpoints():
    print("Testing API Endpoints...\n")
    
    # 1. Test if server is running
    print("1. Testing server connection...")
    try:
        response = requests.get(f"{BASE_URL}/auth/me")
        print(f"   Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n2. Testing all endpoints (without auth):")
    
    endpoints = [
        ("GET", "/auth/me"),
        ("POST", "/auth/login"),
        ("POST", "/auth/register"),
        ("GET", "/cases"),
        ("GET", "/files/recent"),
        ("GET", "/search"),
        ("GET", "/backup"),
        ("GET", "/users/pending"),
        ("GET", "/reports/dashboard"),
    ]
    
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={})
            
            print(f"   {method} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   {method} {endpoint}: ERROR - {e}")
    
    print("\n3. Testing CORS headers...")
    try:
        response = requests.get(f"{BASE_URL}/auth/me")
        headers = response.headers
        print("   CORS Headers found:")
        for key in headers:
            if 'access-control' in key.lower() or 'cors' in key.lower():
                print(f"   {key}: {headers[key]}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    test_endpoints()