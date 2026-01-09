import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('Missing Supabase environment variables')
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Checking database...")

# Check user_reporting table
try:
    response = supabase.table('user_reporting').select('*').execute()
    print(f'User reporting records: {len(response.data)}')
    for record in response.data:
        print(f'  Manager: {record["manager_id"][:8]}..., Employee: {record["employee_id"][:8]}...')
except Exception as e:
    print(f'Error checking user_reporting: {e}')

# Check user_miles table
try:
    response = supabase.table('user_miles').select('*').execute()
    print(f'User miles records: {len(response.data)}')
    for user in response.data:
        print(f'  ID: {user["auth_id"][:8]}..., Name: {user["name"]}, Role: {user["role"]}')
except Exception as e:
    print(f'Error checking user_miles: {e}')

