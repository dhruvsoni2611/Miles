#!/usr/bin/env python3
"""
Test script to verify Supabase connection and Miles schema tables
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection and query Miles schema tables"""
    try:
        # Get environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        print("Environment variables loaded:")
        print(f"SUPABASE_URL: {'[OK]' if supabase_url else '[MISSING]'}")
        print(f"SUPABASE_SERVICE_ROLE_KEY: {'[OK]' if supabase_service_key else '[MISSING]'}")

        if not supabase_url or not supabase_service_key:
            print("ERROR: Missing environment variables")
            print("Please ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in .env file")
            return False

        print("\nConnecting to Supabase...")
        supabase: Client = create_client(supabase_url, supabase_service_key)

        print("[SUCCESS] Supabase client created successfully")

        # Test connection by checking tables
        tables_to_check = ['user_miles', 'user_reporting', 'tasks', 'projects']
        print("\nChecking database tables:")

        all_tables_exist = True
        for table in tables_to_check:
            try:
                response = supabase.table(table).select('*').limit(1).execute()
                has_data = len(response.data) > 0 if response.data else False
                print(f"[OK] {table}: exists, has_data={has_data}")
            except Exception as e:
                print(f"[ERROR] {table}: {str(e)}")
                all_tables_exist = False

        if not all_tables_exist:
            print("\n[WARNING] Some tables are missing. Please run the schema.sql in Supabase SQL Editor.")
            return False

        print("\n[SUCCESS] Database connection and schema verification completed!")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {e}")
        return False

if __name__ == "__main__":
    print("Testing Supabase connection and Miles schema...")
    print("=" * 60)

    success = test_supabase_connection()

    print("=" * 60)
    if success:
        print("[SUCCESS] All tests passed! Ready to use Supabase connection.")
    else:
        print("[FAILED] Test failed. Please check your configuration.")
        print("\nTroubleshooting:")
        print("1. Verify .env file has correct Supabase credentials")
        print("2. Ensure schema.sql has been run in Supabase SQL Editor")
        print("3. Check Supabase project is active and accessible")
