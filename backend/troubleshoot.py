#!/usr/bin/env python3
"""
Troubleshooting script for Miles backend issues
"""

import os
import sys
import requests
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("🔍 Checking .env file...")

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("💡 Run: python quick_setup.py")
        return False

    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]

    missing_vars = []
    placeholder_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif 'your-' in value.lower() or 'here' in value.lower():
            placeholder_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False

    if placeholder_vars:
        print(f"⚠️  Placeholder values found in: {', '.join(placeholder_vars)}")
        print("💡 Update these with your actual Supabase credentials")
        return False

    print("✅ .env file looks good")
    return True

def check_imports():
    """Check if required packages can be imported"""
    print("\n🔍 Checking imports...")

    try:
        from fastapi import FastAPI
        from supabase import create_client
        from pydantic import BaseModel
        print("✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_supabase_connection():
    """Test Supabase connection"""
    print("\n🔍 Testing Supabase connection...")

    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            print("❌ Supabase credentials not found")
            return False

        supabase = create_client(url, key)

        # Try a simple query to test connection
        response = supabase.table("user_miles").select("*").limit(1).execute()
        print("✅ Supabase connection successful")
        return True

    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print("💡 Check your credentials and ensure the database schema is applied")
        return False

def check_backend_server():
    """Check if backend server is running"""
    print("\n🔍 Checking backend server...")

    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"⚠️  Backend server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend server not running")
        print("💡 Start server with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

def test_task_creation_api():
    """Test task creation API"""
    print("\n🔍 Testing task creation API...")

    task_data = {
        "title": "Test Task",
        "description": "Testing API connectivity",
        "priority": "medium",
        "difficulty_level": 2,
        "status": "todo"
    }

    try:
        response = requests.post(
            "http://localhost:8000/api/tasks",
            json=task_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Task creation API working!")
            print(f"   Created task: {result['data']['title']}")
            return True
        else:
            error_data = response.json()
            print(f"❌ API returned error: {response.status_code}")
            print(f"   Details: {error_data}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend API")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Run all checks"""
    print("🔧 Miles Backend - Troubleshooting")
    print("=" * 50)

    checks = [
        ("Environment Configuration", check_env_file),
        ("Python Imports", check_imports),
        ("Supabase Connection", check_supabase_connection),
        ("Backend Server", check_backend_server),
        ("Task Creation API", test_task_creation_api),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        result = check_func()
        results.append((check_name, result))

    print("\n" + "=" * 50)
    print("📊 TROUBLESHOOTING SUMMARY")
    print("=" * 50)

    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 All checks passed! Your backend should be working.")
    else:
        print("\n⚠️  Some checks failed. Fix the issues above and try again.")
        print("\n💡 Quick fix commands:")
        print("   python quick_setup.py    # Set up .env file")
        print("   python main.py          # Start backend server")
        print("   python troubleshoot.py  # Run this again")

if __name__ == "__main__":
    main()

