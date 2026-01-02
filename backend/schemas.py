from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone

# User Task Creation Schema
class UserTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Task title (1-255 characters)")
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: str = Field("medium", pattern="^(low|medium|high|urgent)$", description="Task priority level")
    status: str = Field("assigned", pattern="^(pending|assigned|in_progress|in_review|completed|cancelled)$", description="Task status")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage (0-100)")
    notes: Optional[str] = None
    tags: Optional[List[str]] = []

    @validator('deadline')
    def deadline_must_be_future(cls, v):
        if v is not None:
            # Ensure both datetimes are timezone-aware for comparison
            now = datetime.now(timezone.utc)
            if v.tzinfo is None:
                # If v is naive, assume it's in UTC
                v = v.replace(tzinfo=timezone.utc)

            if v <= now:
                raise ValueError('Deadline must be in the future')
        return v
