#!/usr/bin/env python3

import sys
import os

# Add backend directory to path
backend_dir = os.path.dirname(__file__)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Mock environment variables
os.environ['SUPABASE_URL'] = 'test'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test'

def test_imports():
    try:
        print('Testing schema import...')
        from schemas import UserTaskCreate
        print('SUCCESS: Schema imported successfully')

        print('Testing router import...')
        from routers.employee_management import router
        print('SUCCESS: Router imported successfully')

        routes = [route.path for route in router.routes]
        print(f'SUCCESS: Router has routes: {routes}')

        print('SUCCESS: All imports working!')

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
