#!/usr/bin/env python3
"""
Test the assignment endpoint to verify it works
"""
import requests
import json

def test_assignment_endpoint():
    """Test the assignment endpoint"""
    try:
        # Test data
        assignment_data = {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "assigned_by": "550e8400-e29b-41d4-a716-446655440002",
            "assigned_at": "2024-01-01T12:00:00.000Z"
        }

        print("Testing assignment endpoint...")
        print(f"Data: {assignment_data}")

        # Make request (without auth for testing)
        response = requests.post(
            "http://localhost:8000/api/assignments",
            json=assignment_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 401:
            print("✅ Endpoint exists (401 = auth required, which is expected)")
        elif response.status_code == 200:
            print("✅ Endpoint works and processed request")
        else:
            print(f"❌ Unexpected status: {response.status_code}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_assignment_endpoint()

