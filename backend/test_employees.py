#!/usr/bin/env python3
"""
Test script to create sample employees and manager relationships
"""
import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('❌ Missing Supabase environment variables')
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_test_data():
    print("🧪 Creating test employees...")

    # Create test manager
    manager_id = str(uuid.uuid4())
    manager_auth_id = str(uuid.uuid4())

    # Create test employees
    employee1_auth_id = str(uuid.uuid4())
    employee2_auth_id = str(uuid.uuid4())

    try:
        print(f"👔 Creating manager: {manager_auth_id}")
        # Insert manager
        supabase.table('user_miles').insert({
            'auth_id': manager_auth_id,
            'email': 'manager@test.com',
            'name': 'Test Manager',
            'role': 'admin'
        }).execute()

        print(f"👤 Creating employee 1: {employee1_auth_id}")
        # Insert employees
        supabase.table('user_miles').insert([
            {
                'auth_id': employee1_auth_id,
                'email': 'john.doe@test.com',
                'name': 'John Doe',
                'role': 'employee'
            },
            {
                'auth_id': employee2_auth_id,
                'email': 'jane.smith@test.com',
                'name': 'Jane Smith',
                'role': 'employee'
            }
        ]).execute()

        print("🔗 Creating reporting relationships")
        # Create reporting relationships
        supabase.table('user_reporting').insert([
            {
                'employee_id': employee1_auth_id,
                'manager_id': manager_auth_id,
                'assigned_by': manager_auth_id
            },
            {
                'employee_id': employee2_auth_id,
                'manager_id': manager_auth_id,
                'assigned_by': manager_auth_id
            }
        ]).execute()

        print("✅ Test data created successfully!")
        print("\n📋 Test Credentials:")
        print(f"Manager Email: manager@test.com")
        print(f"Manager Auth ID: {manager_auth_id}")
        print("\n👥 Employees created:")
        print("- John Doe (john.doe@test.com)")
        print("- Jane Smith (jane.smith@test.com)")
        print("\n💡 To test: Login with manager@test.com, then go to Team page and click 'Refresh'")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_data()

