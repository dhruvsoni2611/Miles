#!/usr/bin/env python3
"""
Check if skills exist in the database
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

def check_skills():
    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )

        # Check if skills exist
        response = supabase.table('skills').select('*').limit(10).execute()
        skills = response.data or []

        print(f"Found {len(skills)} skills in database")

        if skills:
            print("Sample skills:")
            for skill in skills[:5]:
                print(f"  - {skill['name']} ({skill.get('category', 'No category')})")
        else:
            print("No skills found. Populating with sample skills...")

            # Sample skills to populate
            sample_skills = [
                {"name": "Python", "category": "Programming Languages"},
                {"name": "JavaScript", "category": "Programming Languages"},
                {"name": "React", "category": "Frontend Frameworks"},
                {"name": "Node.js", "category": "Backend Frameworks"},
                {"name": "SQL", "category": "Databases"},
                {"name": "Machine Learning", "category": "AI/ML"},
                {"name": "Project Management", "category": "Management"},
                {"name": "UI/UX Design", "category": "Design"},
                {"name": "DevOps", "category": "Infrastructure"},
                {"name": "Testing", "category": "Quality Assurance"}
            ]

            # Insert sample skills
            for skill in sample_skills:
                supabase.table('skills').insert(skill).execute()

            print(f"✅ Populated database with {len(sample_skills)} sample skills")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_skills()