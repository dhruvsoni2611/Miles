import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Get environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('Missing Supabase environment variables')
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Creating test data...")

# Create a test manager (admin)
manager_id = str(uuid.uuid4())
manager_auth_id = str(uuid.uuid4())

# Create test employees
employee1_auth_id = str(uuid.uuid4())
employee2_auth_id = str(uuid.uuid4())

print(f"Manager auth_id: {manager_auth_id}")
print(f"Employee1 auth_id: {employee1_auth_id}")
print(f"Employee2 auth_id: {employee2_auth_id}")

try:
    # Insert manager
    supabase.table('user_miles').insert({
        'auth_id': manager_auth_id,
        'email': 'manager@test.com',
        'name': 'Test Manager',
        'role': 'admin'
    }).execute()
    print("Manager created")

    # Insert employees
    supabase.table('user_miles').insert([
        {
            'auth_id': employee1_auth_id,
            'email': 'employee1@test.com',
            'name': 'John Doe',
            'role': 'employee'
        },
        {
            'auth_id': employee2_auth_id,
            'email': 'employee2@test.com',
            'name': 'Jane Smith',
            'role': 'employee'
        }
    ]).execute()
    print("Employees created")

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
    print("Reporting relationships created")

    print("\nTest data created successfully!")
    print("Manager login credentials: manager@test.com")
    print("Use these auth_ids for testing in the frontend")

except Exception as e:
    print(f"Error creating test data: {e}")
    import traceback
    traceback.print_exc()

