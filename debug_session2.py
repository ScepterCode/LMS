#!/usr/bin/env python3
"""Check existing sessions and try simpler creation approach"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiZGQzY2NlZC0zYzA2LTRlZGEtYjYzMi03YmY3YTRmMDNiM2UiLCJlbWFpbCI6ImFkbWluQGRlbW9oaWdoc2Nob29sLmVkdS5uZyIsInJvbGUiOiJhZG1pbiIsInNjaG9vbF9pZCI6IjUxYTE1MzQ5LTQ3ZjktNDQ0OS1hZTYzLTNkYWFmMTZkZTA0ZSIsInVzZXJfdHlwZSI6InVzZXIiLCJleHAiOjE3ODI3NTk5MTMsImlhdCI6MTc4MjY3MzUxM30.QgmI6DGnlgwho_YeT9kzg7RT-CDiX4XZDsMdyRW878U'

headers = {"Authorization": f"Bearer {token}"}

print("Listing existing sessions...")
response = requests.get(f"{BASE_URL}/sessions", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Now try creating a session with is_current = False (to avoid the update)
print("\n\nAttempting to create session with is_current=False (to avoid update timeout)...")
response = requests.post(
    f"{BASE_URL}/sessions",
    headers=headers,
    json={
        "name": "2024/2025",
        "start_date": "2024-09-01",
        "end_date": "2025-07-31",
        "is_current": False  # Don't set as current to avoid update operation
    },
    timeout=30
)

print(f"Status Code: {response.status_code}")
if response.status_code in [200, 201]:
    data = response.json()
    print(f"\n✓ Session created successfully!")
    print(f"Session ID: {data.get('id')}")
else:
    print(f"Response: {response.text}")
