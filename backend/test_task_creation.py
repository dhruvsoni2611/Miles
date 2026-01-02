#!/usr/bin/env python3
"""
Test script to verify task creation works with real Supabase database
"""
import os
import sys
import requests
from datetime import datetime, timezone

def test_task_creation():
    """Test creating a task via the API"""

    # Backend URL
    base_url = "http://localhost:8000"

    # Test data
    task_data = {
        "title": "Integration Test Task",
        "description": "Testing real database integration",
        "priority": "high",
        "difficulty_level": 4,
        "required_skills": ["Python", "FastAPI", "Supabase"],
        "status": "todo",
        "due_date": (datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)).isoformat()
    }

    print("🧪 Testing Task Creation with Real Database")
    print("=" * 50)
    print(f"API URL: {base_url}/api/tasks")
    print(f"Task Data: {task_data}")
    print()

    try:
        # First, try to login to get a token
        print("🔐 Attempting to login for authentication...")
        login_data = {
            "email": "admin@example.com",  # This would need to be a real user
            "password": "password123"
        }

        login_response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            timeout=10
        )

        token = None
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            if token:
                print("✅ Authentication successful, got token")

        if token:
            # Make authenticated API request
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            response = requests.post(f"{base_url}/api/tasks", json=task_data, headers=headers, timeout=10)
        else:
            print("❌ No authentication token available - authentication required")
            print("💡 Create a test user first or use existing credentials")
            return False

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Task created successfully!")
            print(f"Task ID: {result['data']['id']}")
            print(f"Title: {result['data']['title']}")
            print(f"Priority: {result['data']['priority']}")
            print(f"Status: {result['data']['status']}")
            print(f"Is Overdue: {result['data']['is_overdue']}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication required - please login first")
            print("💡 The API now requires authentication")
            return False
        else:
            try:
                error_data = response.json()
                print(f"❌ Task creation failed: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"❌ Task creation failed: HTTP {response.status_code} - {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the backend server running?")
        print("💡 Start the server with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Change to backend directory if not already there
    if not os.path.exists("main.py"):
        os.chdir(os.path.dirname(__file__))

    success = test_task_creation()
    if success:
        print("\n🎉 Real database integration test passed!")
    else:
        print("\n💥 Test failed. Check your setup:")
        print("1. Is the backend server running?")
        print("2. Are Supabase credentials configured?")
        print("3. Is the database schema applied?")
        print("4. Check backend logs for detailed errors")
