#!/usr/bin/env python3
"""
Setup script to configure Supabase credentials for the Miles application.
This script helps you set up your environment variables for database connectivity.
"""

import os
import sys
from pathlib import Path

def setup_supabase_credentials():
    """Interactive setup for Supabase credentials"""

    print("🚀 Miles Application - Supabase Setup")
    print("=" * 50)

    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return

    print("\n📝 Please provide your Supabase credentials:")
    print("(You can find these in your Supabase project settings)")

    # Get Supabase URL
    supabase_url = input("\n🔗 Supabase URL (e.g., https://your-project-ref.supabase.co): ").strip()
    if not supabase_url:
        print("❌ Supabase URL is required!")
        return

    # Get Supabase keys
    supabase_anon_key = input("🔑 Supabase Anon Key: ").strip()
    if not supabase_anon_key:
        print("❌ Supabase Anon Key is required!")
        return

    supabase_service_key = input("🔑 Supabase Service Role Key: ").strip()
    if not supabase_service_key:
        print("❌ Supabase Service Role Key is required!")
        return

    supabase_jwt_secret = input("🔐 Supabase JWT Secret (optional, press Enter to skip): ").strip()

    secret_key = input("🔐 Backend Secret Key (optional, will generate random): ").strip()
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
        print(f"🔑 Generated secret key: {secret_key}")

    # Create .env content
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_anon_key}
SUPABASE_SERVICE_ROLE_KEY={supabase_service_key}
{f'SUPABASE_JWT_SECRET={supabase_jwt_secret}' if supabase_jwt_secret else '# SUPABASE_JWT_SECRET=your-jwt-secret-here'}

# Backend Configuration
SECRET_KEY={secret_key}

# OpenAI API (optional for future features)
OPENAI_API_KEY=your-openai-api-key-here

# Development settings
DEVELOPMENT=true
"""

    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print(f"📁 Location: {os.path.abspath('.env')}")

        # Test the configuration
        print("\n🧪 Testing configuration...")
        test_supabase_connection(supabase_url, supabase_anon_key, supabase_service_key)

    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")

def test_supabase_connection(url, anon_key, service_key):
    """Test Supabase connection"""
    try:
        from supabase import create_client

        # Test anon key connection
        supabase = create_client(url, anon_key)
        print("✅ Supabase anon key connection: OK")

        # Test service key connection
        supabase_admin = create_client(url, service_key)
        print("✅ Supabase service key connection: OK")

        # Test database connection by checking if tasks table exists
        try:
            response = supabase_admin.table("tasks").select("*").limit(1).execute()
            print("✅ Database connection: OK")
            print("🎉 Setup complete! Your backend is ready to use.")
        except Exception as db_error:
            print(f"⚠️  Database connection issue: {db_error}")
            print("💡 Make sure you've run the schema.sql in your Supabase SQL editor")

    except ImportError:
        print("⚠️  Supabase client not installed. Run: pip install supabase")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("💡 Double-check your Supabase credentials")

if __name__ == "__main__":
    # Change to backend directory if not already there
    if not Path("main.py").exists():
        backend_dir = Path(__file__).parent
        os.chdir(backend_dir)

    setup_supabase_credentials()

