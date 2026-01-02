#!/usr/bin/env python3
"""
Quick setup script for Miles backend - creates a minimal .env file for development
"""

import os
from pathlib import Path

def create_minimal_env():
    """Create a minimal .env file for development"""

    env_content = """# Minimal Supabase Configuration for Development
# UPDATE THESE VALUES with your actual Supabase credentials!

SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here

# Backend Configuration
SECRET_KEY=development-secret-key-change-in-production

# OpenAI API (optional)
OPENAI_API_KEY=your-openai-api-key-here

# Development settings
DEVELOPMENT=true
"""

    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists!")
        overwrite = input("Overwrite it? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return

    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("📝 Edit the file with your actual Supabase credentials")
        print("🔗 Get credentials from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api")
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")

def print_setup_instructions():
    """Print setup instructions"""
    print("\n🚀 QUICK SETUP COMPLETE!")
    print("=" * 50)
    print("To get task creation working:")
    print()
    print("1. 📝 Configure Supabase credentials in .env file")
    print("2. 🗄️  Apply database schema:")
    print("   - Go to Supabase SQL Editor")
    print("   - Run contents of ../supabase/schema.sql")
    print("3. ▶️  Start backend: python main.py")
    print("4. 🌐 Test API: python test_task_creation.py")
    print()
    print("❌ If you get errors, check that:")
    print("   - .env file has correct Supabase credentials")
    print("   - Database schema is applied")
    print("   - Backend server is running on port 8000")

if __name__ == "__main__":
    print("🔧 Miles Backend - Quick Setup")
    print("=" * 40)
    create_minimal_env()
    print_setup_instructions()
