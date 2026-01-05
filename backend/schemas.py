from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone

# User Task Creation Schema
class UserTaskCreate(BaseModel):
    title: Optional[str] = Field("Test Task", min_length=1, max_length=255, description="Task title (1-255 characters)")
    description: Optional[str] = None
    project_id: Optional[str] = None  # UUID string for project reference
    priority: str = Field("medium", pattern="^(low|medium|high|urgent)$", description="Task priority level")
    difficulty_level: int = Field(1, ge=1, le=10, description="Task difficulty (1-10)")
    required_skills: Optional[List[str]] = []  # List of skill names
    status: str = Field("todo", pattern="^(todo|in_progress|review|done)$", description="Task status")
    assigned_to: Optional[str] = None  # UUID string for assigned user
    due_date: Optional[datetime] = None  # Changed from deadline to due_date
    notes: Optional[str] = None

    @validator('due_date')
    def due_date_must_be_future(cls, v):
        if v is not None:
            # Ensure both datetimes are timezone-aware for comparison
            now = datetime.now(timezone.utc)
            if v.tzinfo is None:
                # If v is naive, assume it's in UTC
                v = v.replace(tzinfo=timezone.utc)

            if v <= now:
                raise ValueError('Due date must be in the future')
        return v

    # Helper method to convert frontend priority string to database integer
    def get_priority_int(self) -> int:
        priority_map = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4
        }
        return priority_map.get(self.priority, 2)  # default to medium


# Employee Creation Schema
class EmployeeCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, description="Employee email address")
    name: str = Field(..., min_length=1, max_length=255, description="Employee full name")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    skill_vector: Optional[str] = Field("", description="Comma-separated list of employee skills")

    @validator('email')
    def email_must_be_valid(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()  # normalize to lowercase