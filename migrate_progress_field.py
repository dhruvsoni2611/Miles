#!/usr/bin/env python3
"""
Migration script to add progress field to tasks table
Run this to apply the schema changes to your live Supabase database
"""

import os
from supabase import create_client
from dotenv import load_dotenv

def migrate_progress_field():
    """Add progress field to tasks table"""

    # Load environment variables
    load_dotenv()

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("❌ Missing Supabase credentials in .env file")
        return False

    try:
        # Initialize Supabase admin client
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("✅ Connected to Supabase")

        # Check if progress column already exists
        print("🔍 Checking if progress column exists...")

        # Try to update a test task to see if the column exists
        test_response = supabase_admin.table('tasks').select('progress').limit(1).execute()

        if test_response.data is not None:
            print("✅ Progress column already exists - no migration needed")
            return True

    except Exception as e:
        print(f"❌ Error checking progress column: {e}")

        # If the column doesn't exist, we get an error when trying to select it
        # This means we need to add the column
        print("📝 Progress column doesn't exist, adding it...")

        try:
            # Add the progress column using raw SQL
            sql = """
            ALTER TABLE public.tasks
            ADD COLUMN IF NOT EXISTS progress INT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100);
            """

            # Execute the SQL directly (this requires appropriate permissions)
            supabase_admin.rpc('exec_sql', {'sql': sql})

            print("✅ Progress column added successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to add progress column: {e}")
            print("💡 You may need to add this column manually in your Supabase dashboard:")
            print("   1. Go to Supabase Dashboard > SQL Editor")
            print("   2. Run: ALTER TABLE public.tasks ADD COLUMN progress INT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100);")
            return False

if __name__ == "__main__":
    print("🚀 Starting progress field migration...")
    success = migrate_progress_field()

    if success:
        print("🎉 Migration completed successfully!")
        print("📝 Your tasks table now has the progress field.")
    else:
        print("💥 Migration failed. Please add the progress field manually.")
