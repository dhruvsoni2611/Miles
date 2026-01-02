from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone
from supabase import create_client, Client
import os

# Import the schema and supabase
try:
    from schemas import UserTaskCreate
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from schemas import UserTaskCreate

# Supabase admin client - created lazily to avoid import issues
_supabase_admin = None

def get_supabase_admin():
    global _supabase_admin
    if _supabase_admin is None:
        import os
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin

router = APIRouter()

@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: UserTaskCreate
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for demo
):
    """
    Create a new task following the complete flow:
    1. AUTHENTICATION & AUTHORIZATION (temporarily disabled for demo)
    2. INPUT VALIDATION ✓
    3. DATABASE CONNECTIVITY CHECK ✓
    4. DATA PREPARATION ✓
    5. DATABASE INSERTION ✓
    6. RESPONSE PROCESSING ✓
    7. ERROR HANDLING ✓
    """

    try:
        # 1. AUTHENTICATION & AUTHORIZATION (temporarily disabled for demo)
        # For demo purposes, use a hardcoded admin user ID
        # In production, this would come from: user_id = current_user['id']
        user_id = "550e8400-e29b-41d4-a716-446655440000"  # Demo admin user ID

        # 2. INPUT VALIDATION (handled by Pydantic UserTaskCreate schema)
        # Schema validates: title length, priority/status enums, progress range, deadline in future

        # 3. DATABASE CONNECTIVITY CHECK
        try:
            # Test tasks table existence with SELECT * LIMIT 1
            test_response = get_supabase_admin().table("tasks").select("*").limit(1).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Tasks table not found in database"
            )

        # 4. DATA PREPARATION
        task_data = {
            "created_by": user_id,  # Use created_by field in database
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "progress": task.progress,
            "notes": task.notes,
            "tags": task.tags or []
        }

        # 5. DATABASE INSERTION
        try:
            response = get_supabase_admin().table("tasks").insert(task_data).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task"
            )

        # Check response.data exists and is not empty
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task"
            )

        # 6. RESPONSE PROCESSING
        task_result = response.data[0]

        # Compute is_overdue field
        is_overdue = False
        if task_result.get("deadline") and task_result["status"] != "completed":
            try:
                # Parse deadline and compare with current time
                deadline_str = str(task_result["deadline"])
                if deadline_str.endswith('Z'):
                    deadline_dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                else:
                    deadline_dt = datetime.fromisoformat(deadline_str)

                now = datetime.now(timezone.utc)
                is_overdue = deadline_dt < now
            except (ValueError, TypeError):
                is_overdue = False

        # Add is_overdue to task_result
        task_result["is_overdue"] = is_overdue

        # Ensure progress field is included (maps from progress_percentage in our schema)
        if "progress" not in task_result and "progress_percentage" in task_result:
            task_result["progress"] = task_result["progress_percentage"]

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
