"""Test full authentication flow with cookies"""
import requests
import json

def test_auth_flow():
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("\n🔐 Step 1: Login")
    print("=" * 60)
    
    login_response = session.post(
        f"{base_url}/auth/login",
        json={
            "email": "sarahchidiloveday@gmail.com",
            "password": "Admin123!"
        }
    )
    
    print(f"Status: {login_response.status_code}")
    if login_response.status_code == 200:
        print("✅ Login successful!")
        login_data = login_response.json()
        print(f"User: {login_data['user']['full_name']} ({login_data['user']['role']})")
        print(f"School ID: {login_data['user']['school_id']}")
        print(f"\nCookies set: {session.cookies.get_dict()}")
    else:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    print("\n\n📊 Step 2: Get Sessions (should work with cookie)")
    print("=" * 60)
    
    sessions_response = session.get(f"{base_url}/sessions")
    
    print(f"Status: {sessions_response.status_code}")
    if sessions_response.status_code == 200:
        print("✅ Sessions retrieved successfully!")
        sessions = sessions_response.json()
        print(f"Found {len(sessions)} sessions")
        for s in sessions:
            print(f"  - {s['name']} ({'Current' if s.get('is_current') else 'Not current'})")
    else:
        print(f"❌ Failed to get sessions: {sessions_response.text}")
    
    print("\n\n➕ Step 3: Create Session (should work with cookie)")
    print("=" * 60)
    
    create_response = session.post(
        f"{base_url}/sessions",
        json={
            "name": "2024/2025",
            "start_date": "2024-09-01",
            "end_date": "2025-07-31",
            "is_current": True
        }
    )
    
    print(f"Status: {create_response.status_code}")
    if create_response.status_code == 201:
        print("✅ Session created successfully!")
        new_session = create_response.json()
        print(f"Created: {new_session['name']}")
        print(f"ID: {new_session['id']}")
    else:
        print(f"❌ Failed to create session: {create_response.text}")
    
    print("\n\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"Login: {'✅' if login_response.status_code == 200 else '❌'}")
    print(f"Get Sessions: {'✅' if sessions_response.status_code == 200 else '❌'}")
    print(f"Create Session: {'✅' if create_response.status_code == 201 else '❌'}")
    
    if all([
        login_response.status_code == 200,
        sessions_response.status_code == 200,
        create_response.status_code == 201
    ]):
        print("\n🎉 ALL TESTS PASSED! Backend auth flow works perfectly!")
        print("\nThe issue is in the FRONTEND - cookies are not being sent from the browser.")
        print("\nNext step: Check browser dev tools to see if cookies are being set.")
    else:
        print("\n⚠️  Some tests failed. See details above.")

if __name__ == "__main__":
    test_auth_flow()
