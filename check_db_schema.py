#!/usr/bin/env python3
"""
Check current database schema and provide migration commands
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def check_tasks_schema():
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )

        # Try to get a task to see what columns exist
        response = supabase.table('tasks').select('*').limit(1).execute()

        if response.data and len(response.data) > 0:
            task = response.data[0]
            columns = list(task.keys())
            print('📋 Current tasks table columns:')
            for col in sorted(columns):
                print(f'   - {col}')

            # Check for missing columns
            required_columns = ['difficulty_level', 'skill_vector', 'required_skills', 'progress']
            missing = [col for col in required_columns if col not in columns]

            if missing:
                print(f'\n❌ Missing columns: {missing}')
                print('\n🔧 Run these SQL commands in your Supabase SQL editor:')
                print()
                if 'difficulty_level' in missing:
                    print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS difficulty_level INT DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 10);')
                if 'skill_vector' in missing:
                    print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS skill_vector JSONB;')
                if 'required_skills' in missing:
                    print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS required_skills JSONB;')
                if 'progress' in missing:
                    print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS progress INT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100);')
                print()
                print('📝 After running these commands, you may need to refresh your browser or restart your backend.')
            else:
                print('\n✅ All required columns are present')
        else:
            print('📋 Tasks table exists but is empty')
            print('\n🔧 Run these SQL commands to add missing columns:')
            print()
            print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS difficulty_level INT DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 10);')
            print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS skill_vector JSONB;')
            print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS required_skills JSONB;')
            print('ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS progress INT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100);')

    except Exception as e:
        print(f'❌ Error checking database: {e}')
        print('\n🔧 If this is a connection error, make sure your .env file has the correct SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY')

if __name__ == "__main__":
    check_tasks_schema()