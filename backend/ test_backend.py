# test_backend.py
import requests
import json

BASE_URL = "http://localhost:5000/api"

def print_response(name, response):
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text[:200]}")
    
    # Print CORS headers
    cors_headers = {k: v for k, v in response.headers.items() 
                    if 'access-control' in k.lower() or 'cors' in k.lower()}
    if cors_headers:
        print(f"\nCORS Headers:")
        for k, v in cors_headers.items():
            print(f"  {k}: {v}")

def test_backend():
    print("🧪 Testing Judiciary System Backend")
    print("="*60)
    
    # Test 1: Check if server is running
    print("\n1. Testing server status...")
    try:
        response = requests.get("http://localhost:5000/")
        print_response("Server Status", response)
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to server - {e}")
        return
    
    # Test 2: Test admin login
    print("\n2. Testing admin login...")
    login_data = {
        "email": "admin@judiciary.go.ke",
        "password": "Admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                                json=login_data,
                                headers={"Content-Type": "application/json"})
        print_response("Admin Login", response)
        
        # Extract token if login successful
        if response.status_code == 200:
            token = response.json().get("access_token")
            auth_header = {"Authorization": f"Bearer {token}"}
            print(f"\n✅ Login successful! Token acquired.")
            
            # Test 3: Get current user
            print("\n3. Testing GET /auth/me with token...")
            response = requests.get(f"{BASE_URL}/auth/me", headers=auth_header)
            print_response("Current User", response)
            
            # Test 4: Get cases
            print("\n4. Testing GET /cases with token...")
            response = requests.get(f"{BASE_URL}/cases", headers=auth_header)
            print_response("Cases", response)
            
            # Test 5: Get case statistics
            print("\n5. Testing GET /cases/statistics...")
            response = requests.get(f"{BASE_URL}/cases/statistics", headers=auth_header)
            print_response("Case Statistics", response)
            
            # Test 6: Get reports
            print("\n6. Testing GET /reports/dashboard...")
            response = requests.get(f"{BASE_URL}/reports/dashboard", headers=auth_header)
            print_response("Dashboard Report", response)
            
            # Test 7: Get backup
            print("\n7. Testing GET /backup...")
            response = requests.get(f"{BASE_URL}/backup", headers=auth_header)
            print_response("Backup List", response)
            
        else:
            print(f"\n❌ Login failed. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR during login test: {e}")
    
    # Test CORS with preflight request
    print("\n8. Testing CORS Preflight...")
    try:
        response = requests.options(
            f"{BASE_URL}/auth/me",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, Content-Type"
            }
        )
        print_response("CORS Preflight", response)
    except Exception as e:
        print(f"❌ CORS Preflight Error: {e}")

if __name__ == "__main__":
    test_backend()