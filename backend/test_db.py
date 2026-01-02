#!/usr/bin/env python3
"""
Test script to verify Supabase connection and task_admins table
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection and query task_admins table"""
    try:
        # Get environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            print("ERROR: Missing environment variables")
            print("Please ensure SUPABASE_URL and SUPABASE_ANON_KEY are set in .env file")
            return False

        print("Connecting to Supabase...")
        supabase: Client = create_client(supabase_url, supabase_key)

        print("Querying task_admins table...")
        response = supabase.table('task_admins').select('*').execute()

        if response.data:
            print(f"SUCCESS: Retrieved {len(response.data)} users from task_admins table")
            for user in response.data:
                print(f"  - {user['username']} ({user['role']}) - {'Active' if user['is_active'] else 'Inactive'}")
            return True
        else:
            print("WARNING: No data found in task_admins table")
            print("Please ensure the table exists and has data")
            return False

    except Exception as e:
        print(f"ERROR: Failed to connect to Supabase: {e}")
        return False

if __name__ == "__main__":
    print("Testing Supabase connection and task_admins table...")
    print("=" * 50)

    success = test_supabase_connection()

    print("=" * 50)
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed. Please check your configuration.")
