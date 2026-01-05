#!/usr/bin/env python3
"""
Simple test to check assignments table
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_assignments_table():
    """Simple test to check if assignments table has data"""
    try:
        # Import required modules
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()

        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            print("ERROR: Missing Supabase credentials")
            return

        # Create client
        supabase = create_client(supabase_url, supabase_key)

        # Check assignments table
        print("Checking assignments table...")
        result = supabase.table("assignments").select("*").limit(10).execute()

        if result.data:
            print(f"SUCCESS: Found {len(result.data)} assignment records")
            for i, assignment in enumerate(result.data, 1):
                print(f"Assignment {i}:")
                print(f"  task_id: {assignment['task_id']}")
                print(f"  user_id: {assignment['user_id']}")
                print(f"  assigned_by: {assignment['assigned_by']}")
                print(f"  assigned_at: {assignment['assigned_at']}")
        else:
            print("INFO: No assignment records found in database")

        # Check tasks table for assigned tasks
        print("\nChecking tasks with assignments...")
        tasks_result = supabase.table("tasks").select("*").not_("assigned_to", "is", None).limit(5).execute()

        if tasks_result.data:
            print(f"Found {len(tasks_result.data)} tasks with assignments:")
            for i, task in enumerate(tasks_result.data, 1):
                print(f"Task {i}: {task['title']} -> assigned to {task['assigned_to']}")
        else:
            print("No tasks found with assignments")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_assignments_table()
