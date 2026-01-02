from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone
from supabase import create_client, Client
import os

# Import the schema and supabase
try:
    from schemas import UserTaskCreate
    from main import get_current_user
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from schemas import UserTaskCreate
    from main import get_current_user

# Supabase admin client - created lazily to avoid import issues
_supabase_admin = None

def get_supabase_admin():
    global _supabase_admin
    if _supabase_admin is None:
        # Try to get from main module first
        try:
            from main import supabase_admin
            if supabase_admin is not None:
                _supabase_admin = supabase_admin
                return _supabase_admin
        except ImportError:
            pass

        # Fallback to manual initialization
        import os
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")

        try:
            _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except Exception as e:
            raise ValueError(f"Failed to initialize Supabase admin client: {e}")
    return _supabase_admin

router = APIRouter()

@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: UserTaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new task following the complete flow:
    1. AUTHENTICATION & AUTHORIZATION ✓
    2. INPUT VALIDATION ✓
    3. DATABASE CONNECTIVITY CHECK ✓
    4. DATA PREPARATION ✓
    5. DATABASE INSERTION ✓
    6. RESPONSE PROCESSING ✓
    7. ERROR HANDLING ✓
    """

    try:
        # 1. AUTHENTICATION & AUTHORIZATION
        # Get the authenticated user ID from Supabase
        user_id = current_user.id

        # 2. INPUT VALIDATION (handled by Pydantic UserTaskCreate schema)
        # Schema validates: title length, priority/status enums, progress range, deadline in future

        # 3. DATABASE CONNECTIVITY CHECK
        try:
            # Test tasks table existence with SELECT * LIMIT 1
            test_response = get_supabase_admin().table("tasks").select("*").limit(1).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed or tasks table not found"
            )

        # 4. DATA PREPARATION
        task_data = {
            "created_by": user_id,  # Use created_by field in database
            "title": task.title,
            "description": task.description,
            "project_id": task.project_id,  # UUID string for project reference
            "priority": task.get_priority_int(),  # Convert string to integer (1-5)
            "difficulty_level": task.difficulty_level,  # 1-10 scale
            "required_skills": task.required_skills or [],  # JSONB array of skill names
            "status": task.status,  # Must be: todo, in_progress, review, done
            "assigned_to": task.assigned_to,  # UUID string for assigned user
            "due_date": task.due_date.isoformat() if task.due_date else None,  # Changed from deadline
            # "notes": task.notes  # Temporarily removed until schema is updated
        }

        # 5. DATABASE INSERTION
        try:
            response = get_supabase_admin().table("tasks").insert(task_data).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create task: {str(e)}"
            )

        # Check response.data exists and is not empty
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Task creation failed - no data returned from database"
            )

        # 6. RESPONSE PROCESSING
        task_result = response.data[0]

        # Compute is_overdue field
        is_overdue = False
        if task_result.get("due_date") and task_result["status"] != "done":
            try:
                # Parse due_date and compare with current time
                due_date_str = str(task_result["due_date"])
                if due_date_str.endswith('Z'):
                    due_date_dt = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                else:
                    due_date_dt = datetime.fromisoformat(due_date_str)

                now = datetime.now(timezone.utc)
                is_overdue = due_date_dt < now
            except (ValueError, TypeError):
                is_overdue = False

        # Add is_overdue to task_result
        task_result["is_overdue"] = is_overdue

        # 7. SUCCESS RESPONSE
        return {
            "success": True,
            "message": "Task created successfully",
            "data": task_result
        }

    # 7. ERROR HANDLING
    except HTTPException:
        raise
    except Exception as e:
        # Log error and return 500
        print(f"Task creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating task"
        )
