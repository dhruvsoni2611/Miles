from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime, timezone

# User Task Creation Schema
class UserTaskCreate(BaseModel):
    title: Optional[str] = Field("Test Task", min_length=1, max_length=255, description="Task title (1-255 characters)")
    description: Optional[str] = None
    project_id: Optional[str] = None  # UUID string for project reference
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$", description="Task priority level (string)")
    priority_score: Optional[int] = Field(None, ge=1, le=5, description="Task priority score (int, 1-5) - alternative to priority")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10, description="Task difficulty (1-10)")
    difficulty_score: Optional[int] = Field(None, ge=1, le=10, description="Task difficulty score (1-10) - alternative to difficulty_level")
    required_skills: Optional[List[str]] = []  # List of skill names
    status: str = Field("todo", pattern="^(todo|in_progress|review|done)$", description="Task status")
    assigned_to: Optional[str] = None  # UUID string for assigned user
    due_date: Optional[datetime] = None  # Changed from deadline to due_date
    notes: Optional[str] = None
    rating_score: Optional[int] = Field(0, description="Rating score")
    justified: Optional[bool] = Field(False, description="Justified flag")
    bonus: Optional[bool] = Field(False, description="Bonus flag")

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
    experience_years: Optional[Dict[str, int]] = Field(default_factory=dict, description="Experience in months for each skill")
    tenure: Optional[Dict[str, int]] = Field(default_factory=dict, description="Tenure in months for each skill at company")

    @validator('email')
    def email_must_be_valid(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()  # normalize to lowercase


# Task Assignment Schema
class TaskAssignment(BaseModel):
    employee_id: Optional[str] = Field(None, description="UUID of the employee to assign the task to (optional for auto assignment)")


# Task Completion Confirmation Schema (no rating needed - auto-calculated)
class TaskCompletionConfirmation(BaseModel):
    confirm: bool = Field(True, description="Confirmation to complete the task")


# Task Completion Data Schema for reward calculation
# Fields are optional to support both simple confirmation and detailed completion data
class TaskCompletionData(BaseModel):
    completed: bool = Field(True, description="Whether the task was completed successfully (default: True)")
    on_time: Optional[bool] = Field(None, description="Whether the task was completed on time (auto-calculated if not provided)")
    user_rating: Optional[int] = Field(None, description="User rating (1-5 scale, optional)")
    good_behavior: bool = Field(False, description="Whether employee showed good behavior")
    rework_required: bool = Field(False, description="Whether rework was required")
    overdue_days: int = Field(0, ge=0, description="Number of days the task was overdue (auto-calculated if not provided)")
    failed: bool = Field(False, description="Whether the task failed completely")
    completion_notes: Optional[str] = Field(None, description="Notes about task completion")
    # Support for simple confirmation format (backward compatibility)
    confirm: Optional[bool] = Field(None, description="Simple confirmation flag - if provided, sets completed=True")