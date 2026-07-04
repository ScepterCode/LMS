"""
Test script to verify sessions API works WITH authentication
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_without_auth():
    """Test WITHOUT authentication - should fail with 403"""
    print("\n1. Testing WITHOUT authentication...")
    response = requests.get(f"{BASE_URL}/api/v1/sessions")
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 403 (Forbidden)")
    print(f"   Result: {'✅ PASS' if response.status_code == 403 else '❌ FAIL'}")
    return response.status_code == 403

def test_with_auth(email, password):
    """Test WITH authentication - should work"""
    print(f"\n2. Testing WITH authentication (login as {email})...")
    
    # Step 1: Login
    login_data = {"email": email, "password": password}
    session = requests.Session()  # Use session to maintain cookies
    
    print("   Step 1: Logging in...")
    login_response = session.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"   ❌ Login FAILED: {login_response.status_code}")
        print(f"   Error: {login_response.text}")
        return False
    
    print(f"   ✅ Login successful")
    
    # Step 2: Get sessions (should work now)
    print("   Step 2: Getting sessions...")
    sessions_response = session.get(f"{BASE_URL}/api/v1/sessions")
    
    print(f"   Status: {sessions_response.status_code}")
    print(f"   Expected: 200 (OK)")
    
    if sessions_response.status_code == 200:
        sessions = sessions_response.json()
        print(f"   ✅ SUCCESS! Found {len(sessions)} sessions")
        return True
    else:
        print(f"   ❌ FAILED: {sessions_response.text}")
        return False

def test_create_session(email, password):
    """Test creating a session WITH authentication"""
    print(f"\n3. Testing session creation WITH authentication...")
    
    # Login first
    session = requests.Session()
    login_response = session.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    
    if login_response.status_code != 200:
        print(f"   ❌ Login FAILED")
        return False
    
    # Create session
    session_data = {
        "name": "2024/2025",
        "start_date": "2024-09-01",
        "end_date": "2025-08-31",
        "is_current": False
    }
    
    print("   Creating session...")
    create_response = session.post(
        f"{BASE_URL}/api/v1/sessions",
        json=session_data
    )
    
    print(f"   Status: {create_response.status_code}")
    
    if create_response.status_code == 201:
        print(f"   ✅ SUCCESS! Session created")
        return True
    else:
        print(f"   ❌ FAILED: {create_response.text}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("SESSION API AUTHENTICATION TEST")
    print("="*60)
    
    # Test 1: Without auth (should fail - this proves security works)
    test1 = test_without_auth()
    
    print("\n" + "="*60)
    print("TO TEST WITH AUTHENTICATION, RUN:")
    print("="*60)
    print("python test_with_auth.py <your_admin_email> <your_password>")
    print("\nExample:")
    print("python test_with_auth.py admin@school.com password123")
    print("\n" + "="*60)
    
    import sys
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
        
        # Test 2: With auth (should work)
        test2 = test_with_auth(email, password)
        
        # Test 3: Create session
        test3 = test_create_session(email, password)
        
        print("\n" + "="*60)
        print("TEST RESULTS:")
        print("="*60)
        print(f"1. Without auth (should fail): {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"2. With auth (should work):    {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"3. Create session:             {'✅ PASS' if test3 else '❌ FAIL'}")
        print("="*60)
        
        if test1 and test2 and test3:
            print("\n🎉 ALL TESTS PASSED!")
            print("The API works perfectly when authenticated.")
            print("The issue is: YOU NEED TO LOG IN via the web interface.")
        else:
            print("\n⚠️  Some tests failed. Check your credentials.")
    else:
        print("\n💡 The 403 error you're seeing is CORRECT behavior")
        print("   It means the API is properly secured.")
        print("   You just need to LOG IN first!")
