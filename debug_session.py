#!/usr/bin/env python3
"""Debug session creation issues"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiZGQzY2NlZC0zYzA2LTRlZGEtYjYzMi03YmY3YTRmMDNiM2UiLCJlbWFpbCI6ImFkbWluQGRlbW9oaWdoc2Nob29sLmVkdS5uZyIsInJvbGUiOiJhZG1pbiIsInNjaG9vbF9pZCI6IjUxYTE1MzQ5LTQ3ZjktNDQ0OS1hZTYzLTNkYWFmMTZkZTE0ZSIsInVzZXJfdHlwZSI6InVzZXIiLCJleHAiOjE3ODI3NTk5MTMsImlhdCI6MTc4MjY3MzUxM30.QgmI6DGnlgwho_YeT9kzg7RT-CDiX4XZDsMdyRW878U'

headers = {"Authorization": f"Bearer {token}"}

print("Attempting to create session...")
response = requests.post(
    f"{BASE_URL}/sessions",
    headers=headers,
    json={
        "name": "2024/2025",
        "start_date": "2024-09-01",
        "end_date": "2025-07-31",
        "is_current": True
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response Text:\n{response.text}")
print(f"\nHeaders:\n{json.dumps(dict(response.headers), indent=2)}")
