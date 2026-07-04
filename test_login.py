"""Test login directly to verify credentials work"""
import sys
sys.path.insert(0, 'backend')

import requests
import json

def test_login():
    print("\n🔐 Testing Login API...")
    
    url = "http://127.0.0.1:8000/api/v1/auth/login"
    credentials = {
        "email": "sarahchidiloveday@gmail.com",
        "password": "Admin123!"
    }
    
    try:
        response = requests.post(url, json=credentials)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ LOGIN SUCCESSFUL!")
            print("Your credentials are correct.")
            print("\n🌐 Now go to http://localhost:3000/login and use these:")
            print(f"   Email: {credentials['email']}")
            print(f"   Password: {credentials['password']}")
        else:
            print("\n❌ LOGIN FAILED!")
            print("There might be an issue with the credentials or backend.")
            
    except Exception as e:
        print(f"\n❌ Error connecting to backend: {e}")
        print("Make sure the backend server is running on port 8000")

if __name__ == "__main__":
    test_login()
