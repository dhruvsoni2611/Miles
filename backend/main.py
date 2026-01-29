from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from dotenv import load_dotenv
from datetime import date, datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Initialize Supabase clients (only if credentials are available)
supabase: Client = None
supabase_admin: Client = None

if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print(f"[SUCCESS] Supabase client initialized with URL: {SUPABASE_URL}")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client: {e}")
        supabase = None

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("[SUCCESS] Supabase admin client initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase admin client: {e}")
        supabase_admin = None

# JWT Configuration (for custom endpoints if needed)
SECRET_KEY = SUPABASE_JWT_SECRET or os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Pydantic Models
class LoginRequest(BaseModel):
    email: str  # Using email for Supabase Auth
    password: str

class SignupRequest(BaseModel):
    email: str  # Using str instead of EmailStr to avoid dependency issues
    password: str
    name: str
    role: str = "admin"  # Default to admin for all signups

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str

# Task-related models
class TaskCompletionConfirmation(BaseModel):
    confirm: bool = Field(True, description="Confirmation to complete the task")

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority_score: int = 1
    difficulty_score: int = 1
    required_skills: Optional[List[str]] = None
    status: str = "todo"
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    rating_score: int = 0
    justified: bool = False
    bonus: bool = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority_score: Optional[int] = None
    difficulty_score: Optional[int] = None
    required_skills: Optional[List[str]] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    progress: Optional[int] = None

class TaskResponse(TaskBase):
    id: str
    created_by: str
    status: str
    created_at: datetime
    updated_at: datetime
    rating_score: int
    justified: bool
    bonus: bool
    is_overdue: Optional[bool] = None

# Employee-related models
class EmployeeBase(BaseModel):
    name: str
    email: str
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    skill_vector: Optional[str] = None
    experience_years: Optional[Dict[str, int]] = Field(default_factory=dict, description="Experience in months for each skill")
    tenure: Optional[Dict[str, int]] = Field(default_factory=dict, description="Tenure in months for each skill at company")

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(EmployeeBase):
    status: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: str
    profile_id: str
    employee_code: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Dashboard stats model
class DashboardStats(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    cancelled_tasks: int = 0
    overdue_tasks: int = 0
    urgent_tasks: int = 0
    high_priority_tasks: int = 0
    total_employees: int = 0
    active_employees: int = 0
    completion_rate: float = 0.0

# Supabase Auth Helper Functions
def get_current_user_from_token(token: str):
    """Get current user from Supabase JWT token"""
    try:
        # Verify the token with Supabase
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            user = user_response.user

            # Query the user_miles table to get additional profile details
            profile_response = supabase.table('user_miles').select('*').eq('auth_id', user.id).execute()

            if profile_response.data and len(profile_response.data) > 0:
                user_profile = profile_response.data[0]

                # Add role information to user metadata
                if not user.user_metadata:
                    user.user_metadata = {}
                user.user_metadata['role'] = user_profile.get('role', 'employee')
                user.user_metadata['name'] = user_profile.get('name', user.email.split('@')[0])
            else:
                # User exists in Supabase Auth but not in user_miles table
                # Set default role
                if not user.user_metadata:
                    user.user_metadata = {}
                user.user_metadata['role'] = 'employee'
                user.user_metadata['name'] = user.email.split('@')[0]

            return user
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        print(f"Token provided: {token[:50]}...")  # Log first 50 chars for debugging
        return None

def get_user_role(user_id: str):
    """Get user role from user_miles table"""
    try:
        # Query the user_miles table for the user's role
        response = supabase.table('user_miles').select('role').eq('auth_id', user_id).execute()

        if response.data and len(response.data) > 0:
            return response.data[0].get('role', 'employee')

        # User exists in Supabase Auth but not in user_miles table
        # Return default role
        return 'employee'
    except Exception as e:
        print(f"Error getting user role: {e}")
        return 'employee'

def update_user_role(user_id: str, role: str):
    """Update user role in metadata"""
    try:
        supabase_admin.auth.admin.update_user_by_id(user_id, {
            'user_metadata': {'role': role}
        })
        return True
    except Exception as e:
        print(f"Error updating user role: {e}")
        return False

def get_current_user(token: str = Depends(HTTPBearer())):
    """Get current authenticated user from Supabase JWT token"""
    try:
        user = get_current_user_from_token(token.credentials)
        if user is None:
            print("User not found for token")
            raise HTTPException(status_code=401, detail="Invalid token or user not found")
        return user
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Security scheme
security = HTTPBearer()

# Initialize FastAPI app
app = FastAPI(
    title="Miles API",
    description="AI-powered backend with LangGraph",
    version="1.0.0"
)

# Include routers
try:
    from routers.employee_management import router as employee_router
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    backend_dir = os.path.dirname(__file__)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    try:
        from routers.employee_management import router as employee_router
    except ImportError as e:
        # Last resort - create empty router to prevent crashes
        from fastapi import APIRouter
        employee_router = APIRouter()
        print(f"Warning: Could not import employee_management router: {e}")

app.include_router(employee_router, prefix="/api", tags=["Employee Management"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check endpoint
@app.get("/")
async def root():
    return {"message": "Miles API is running!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Test endpoints and helper functions removed - use production endpoints instead

# Authentication Endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login using Supabase Auth and check user_miles table for role"""
    try:
        # 1. Authenticate with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })

        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = auth_response.user
        session = auth_response.session

        # 2. Check if user exists in user_miles table
        profile_response = supabase.table('user_miles').select('*').eq('auth_id', user.id).execute()

        if not profile_response.data or len(profile_response.data) == 0:
            # 3. User exists in Supabase Auth but not in user_miles table
            # Create a new profile with default values
            print(f"User {user.email} not found in user_miles table, creating profile...")

            try:
                # Get role from Supabase Auth metadata (set during signup) or default to employee
                user_role_from_metadata = user.user_metadata.get('role', 'employee') if user.user_metadata else 'employee'

                # Insert new user profile using service role (bypasses RLS)
                supabase_admin.table('user_miles').insert({
                    'auth_id': user.id,
                    'email': user.email,
                    'name': user.user_metadata.get('name', user.email.split('@')[0]) if user.user_metadata else user.email.split('@')[0],
                    'role': user_role_from_metadata,  # Use role from signup
                    'profile_picture': None,
                    'skill_vector': None,
                    'productivity_score': 0.0
                }).execute()
                print(f"✅ Created new user profile in user_miles table for: {user.email} (role: {user_role_from_metadata})")
                user_role = user_role_from_metadata
                user_name = user.user_metadata.get('name', user.email.split('@')[0]) if user.user_metadata else user.email.split('@')[0]
            except Exception as profile_error:
                error_msg = str(profile_error).lower()
                # Check if it's a duplicate key error (user already exists)
                if 'duplicate key' in error_msg or 'unique constraint' in error_msg or 'already exists' in error_msg:
                    print(f"✅ User profile already exists (caught duplicate error): {user.email}")
                    # Fetch the existing profile
                    existing_response = supabase_admin.table('user_miles').select('*').eq('auth_id', user.id).execute()
                    if existing_response.data and len(existing_response.data) > 0:
                        user_profile = existing_response.data[0]
                        user_role = user_profile['role']
                        user_name = user_profile['name']
                    else:
                        # Fallback if we can't fetch existing data
                        user_role = 'employee'
                        user_name = user.email.split('@')[0]
                else:
                    print(f"❌ Unexpected error creating user profile: {profile_error}")
                    user_role = 'employee'  # Default fallback
                    user_name = user.email.split('@')[0]
        else:
            # 4. User exists in user_miles table
            user_profile = profile_response.data[0]
            user_role = user_profile['role']
            user_name = user_profile['name']
            print(f"✅ Found existing user profile for: {user.email}")

        # 5. Create user response
        user_response = {
            "id": user.id,
            "email": user.email,
            "name": user_name,
            "role": user_role,
            "is_active": True,
            "created_at": user.created_at
        }

        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user=user_response,
            expires_in=session.expires_in
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/api/auth/google-login")
async def google_login():
    """Handle Google OAuth login - check if Google user exists in user_miles table"""
    try:
        # This endpoint would be called after Google OAuth completes
        # The frontend handles the OAuth flow and then calls this to validate
        return {"message": "Google login endpoint - implement user lookup"}

    except Exception as e:
        print(f"Google login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google login failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/api/auth/signup")
async def signup(signup_data: SignupRequest):
    """Signup using Supabase Auth"""
    try:
        # Sign up with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": signup_data.email,
            "password": signup_data.password,
            "options": {
                "data": {
                    "name": signup_data.name,
                    "role": signup_data.role
                }
            }
        })

        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed",
            )

        user = auth_response.user

        return {
            "message": "Signup successful. Please check your email to confirm your account.",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": signup_data.name,
                "role": signup_data.role
            }
        }

    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup failed",
        )

@app.post("/api/auth/logout")
async def logout(token: str = Depends(HTTPBearer())):
    """Logout endpoint - sign out from Supabase"""
    try:
        # Sign out from Supabase
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        print(f"Logout error: {e}")
        return {"message": "Logged out (with warnings)"}

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.user_metadata.get('name', '') if current_user.user_metadata else '',
        "role": getattr(current_user, 'role', 'employee'),
        "is_active": True,
        "created_at": current_user.created_at
    }

@app.get("/api/auth/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify if the current token is valid"""
    return {"valid": True, "user": get_current_user_info(current_user)}

# Dashboard API
@app.get("/api/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics for the current admin user"""
    try:
        profile_id = current_user.id

        # Get task statistics
        tasks_response = supabase_admin.table('tasks').select('status, priority_score, due_date').eq('created_by', profile_id).execute()
        tasks = tasks_response.data or []

        # Calculate task stats
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        pending_tasks = len([t for t in tasks if t['status'] == 'pending'])
        in_progress_tasks = len([t for t in tasks if t['status'] == 'in_progress'])
        cancelled_tasks = len([t for t in tasks if t['status'] == 'cancelled'])

        # Priority stats (priority_score: 1=low, 2=medium, 3=high, 4=urgent, 5=critical)
        urgent_tasks = len([t for t in tasks if t['priority_score'] >= 4])  # urgent and critical
        high_priority_tasks = len([t for t in tasks if t['priority_score'] == 3])  # high only

        # Overdue tasks (due_date < now and not done)
        now = datetime.utcnow()
        overdue_tasks = len([
            t for t in tasks
            if t.get('due_date') and t['due_date'] and
               datetime.fromisoformat(str(t['due_date']).replace('Z', '+00:00')) < now and
               t['status'] != 'done'
        ])

        # Completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

        # Get employee statistics
        employees_response = supabase.table('employees').select('status, is_active').eq('profile_id', profile_id).execute()
        employees = employees_response.data or []

        total_employees = len(employees)
        active_employees = len([e for e in employees if e['status'] == 'active' and e['is_active']])

        return DashboardStats(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            in_progress_tasks=in_progress_tasks,
            cancelled_tasks=cancelled_tasks,
            overdue_tasks=overdue_tasks,
            urgent_tasks=urgent_tasks,
            high_priority_tasks=high_priority_tasks,
            total_employees=total_employees,
            active_employees=active_employees,
            completion_rate=round(completion_rate, 1)
        )

    except Exception as e:
        print(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard statistics")

# Tasks API - POST /api/tasks is handled by employee_management router (has skill embeddings, workload updates)

@app.get("/api/tasks")
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    overdue: bool = False,
    current_user = Depends(get_current_user)
):
    """Get tasks assigned to the current user with optional filters"""
    try:
        # Filter tasks assigned to the current user
        user_id = current_user.id
        query = supabase_admin.table('tasks').select('*').eq('assigned_to', user_id)

        # Apply filters
        if status:
            query = query.eq('status', status)
        if priority:
            query = query.eq('priority_score', priority)
        if search:
            # Search in title and description using a simpler approach
            search_term = search.lower()
            # We'll filter in Python after fetching
            pass

        response = query.execute()
        tasks = response.data or []

        # Add overdue flag and format response
        now = datetime.utcnow()
        formatted_tasks = []
        for task in tasks:
            task_dict = dict(task)

            if task.get('due_date') and task['due_date']:
                try:
                    due_date_str = str(task['due_date']).replace('Z', '+00:00')
                    due_date_dt = datetime.fromisoformat(due_date_str)
                    task_dict['is_overdue'] = due_date_dt < now and task['status'] != 'done'
                except (ValueError, TypeError):
                    task_dict['is_overdue'] = False
            else:
                task_dict['is_overdue'] = False

            formatted_tasks.append(task_dict)

        # Apply search filter if provided
        if search:
            search_term = search.lower()
            formatted_tasks = [
                t for t in formatted_tasks
                if search_term in t.get('title', '').lower() or
                   search_term in t.get('description', '').lower()
            ]

        # Filter overdue if requested
        if overdue:
            formatted_tasks = [t for t in formatted_tasks if t['is_overdue']]

        return {"tasks": formatted_tasks, "total": len(formatted_tasks)}

    except Exception as e:
        print(f"Get tasks error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


@app.get("/api/tasks/created")
async def get_created_tasks(current_user = Depends(get_current_user)):
    """Get tasks created by the current user"""
    try:
        user_id = current_user.id

        response = supabase_admin.table('tasks').select('*').eq('created_by', user_id).execute()
        tasks = response.data or []

        # Format tasks (reuse the same formatting logic)
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                "id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "priority_score": task["priority_score"],
                "difficulty_score": task["difficulty_score"],
                "project_id": task["project_id"],
                "assigned_to": task["assigned_to"],
                "created_by": task["created_by"],
                "due_date": task["due_date"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
                "rating_score": task.get("rating_score", 0),
                "justified": task.get("justified", False),
                "bonus": task.get("bonus", False),
                "required_skills": task.get("required_skills", []),
                "skill_embedding": task.get("skill_embedding", []),
                "is_overdue": False
            }

            # Calculate if task is overdue
            if task.get("due_date") and task["status"] not in ["completed", "done"]:
                try:
                    due_date = datetime.fromisoformat(task["due_date"].replace('Z', '+00:00'))
                    if due_date < datetime.now(due_date.tzinfo):
                        formatted_task["is_overdue"] = True
                except:
                    pass

            formatted_tasks.append(formatted_task)

        return {"tasks": formatted_tasks, "total": len(formatted_tasks)}

    except Exception as e:
        print(f"Get created tasks error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch created tasks")


@app.get("/api/projects/created")
async def get_created_projects(current_user = Depends(get_current_user)):
    """Get projects created by the current user"""
    try:
        user_id = current_user.id

        response = supabase_admin.table('projects').select('*').eq('created_by', user_id).execute()
        projects = response.data or []

        # Format projects
        formatted_projects = []
        for project in projects:
            formatted_project = {
                "id": project["id"],
                "name": project["name"],
                "description": project["description"],
                "created_by": project["created_by"],
                "deadline": project["deadline"],
                "status": project["status"],
                "created_at": project["created_at"]
            }

            formatted_projects.append(formatted_project)

        return {"projects": formatted_projects, "total": len(formatted_projects)}

    except Exception as e:
        print(f"Get created projects error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch created projects")


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user = Depends(get_current_user)):
    """Get a specific task assigned to the current user"""
    try:
        # Filter task assigned to the current user
        user_id = current_user.id

        response = supabase_admin.table('tasks').select('*').eq('id', task_id).eq('assigned_to', user_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Task not found")

        task = response.data[0]
        return TaskResponse(**task)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Get task error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch task")

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_data: TaskUpdate, current_user = Depends(get_current_user)):
    """Update a task that the user created or is assigned to"""
    try:
        # Check if task exists and user can update it (created by user OR assigned to user)
        user_id = current_user.id
        existing_response = supabase_admin.table('tasks').select('id, status').or_(f'created_by.eq.{user_id},assigned_to.eq.{user_id}').eq('id', task_id).execute()

        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="Task not found or access denied")

        current_task_status = existing_response.data[0]['status']

        # Prevent changing status from 'done' (completed tasks cannot be modified)
        if current_task_status == 'done' and task_data.status and task_data.status != 'done':
            raise HTTPException(status_code=400, detail="Completed tasks cannot be moved to another status")

        # Validate required skills if provided
        if task_data.required_skills is not None and len(task_data.required_skills) > 0:
            # Check if all provided skills exist in the skills table
            skills_response = supabase.table('skills').select('name').in_('name', task_data.required_skills).execute()
            existing_skills = [skill['name'] for skill in skills_response.data or []]

            # Find invalid skills
            invalid_skills = [skill for skill in task_data.required_skills if skill not in existing_skills]

            if invalid_skills:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid skills provided: {', '.join(invalid_skills)}. Please select skills from the available options."
                )

        # Update task
        update_dict = task_data.dict(exclude_unset=True)

        # Convert date/datetime objects to ISO format strings for Supabase
        if 'due_date' in update_dict and isinstance(update_dict['due_date'], datetime):
            update_dict['due_date'] = update_dict['due_date'].isoformat()

        update_dict['updated_at'] = datetime.utcnow().isoformat()

        response = supabase_admin.table('tasks').update(update_dict).eq('id', task_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to update task")

        updated_task = response.data[0]

        # Check if task was completed (status changed to 'done') and record RL feedback
        if 'status' in update_dict and update_dict['status'] == 'done':
            try:
                # Get full task details for RL feedback
                task_details_response = supabase_admin.table('tasks').select(
                    'id, assigned_to, due_date, difficulty_score'
                ).eq('id', task_id).execute()

                if task_details_response.data:
                    task_details = task_details_response.data[0]

                    # Calculate RL metrics
                    r_completion = True
                    r_ontime = True
                    r_hardtask_bonus = task_details.get('difficulty_score', 1) > 5

                    # Calculate overdue days
                    overdue_days = 0
                    if task_details.get('due_date'):
                        due_date = datetime.fromisoformat(task_details['due_date'].replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        if now > due_date:
                            r_ontime = False
                            overdue_days = (now - due_date).days

                    # Insert RL feedback
                    rl_data = {
                        'task_id': task_id,
                        'employee_id': task_details.get('assigned_to'),
                        'r_completion': r_completion,
                        'r_ontime': r_ontime,
                        'r_good_behaviour': False,  # Will be updated by completion rating
                        'p_overdue': overdue_days > 0,
                        'p_rework': 0,
                        'p_failure': False,
                        'r_hardtask_bonus': r_hardtask_bonus
                    }

                    rl_response = supabase_admin.table('rl_miles').insert(rl_data).execute()
                    if rl_response.data:
                        print(f"✅ RL feedback recorded for task {task_id}")
                    else:
                        print(f"⚠️ Failed to record RL feedback for task {task_id}")

            except Exception as e:
                print(f"⚠️ Error recording RL feedback: {e}")
                # Don't fail the task update if RL recording fails

        # Assignment creation is now handled by frontend via separate API call
        # This allows for better error handling and separation of concerns

        return TaskResponse(**updated_task)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Update task error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")


# POST /api/tasks/{task_id}/complete is handled by employee_management router (has RL reward calculation with bandit)


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, current_user = Depends(get_current_user)):
    """Delete a task assigned to the current user"""
    try:
        # Check if task exists and is assigned to the current user
        user_id = current_user.id
        existing_response = supabase_admin.table('tasks').select('id').eq('id', task_id).eq('assigned_to', user_id).execute()

        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="Task not found")

        # Delete task
        response = supabase_admin.table('tasks').delete().eq('id', task_id).eq('assigned_to', user_id).execute()

        return {"message": "Task deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete task error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

# Test endpoints removed - use production endpoints instead

# Create assignment record
@app.post("/api/assignments")
async def create_assignment(assignment: dict, current_user = Depends(get_current_user)):
    """Create an assignment record"""
    try:
        from routers.employee_management import get_supabase_admin
        supabase_client = get_supabase_admin()

        # Validate required fields
        required_fields = ['task_id', 'user_id', 'assigned_by']
        for field in required_fields:
            if field not in assignment:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        assignment_data = {
            'task_id': assignment['task_id'],
            'user_id': assignment['user_id'],
            'assigned_by': assignment['assigned_by'],
            'assigned_at': assignment.get('assigned_at', datetime.utcnow().isoformat())
        }

        print(f"Creating assignment record: {assignment_data}")
        response = supabase_client.table("assignments").insert(assignment_data).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create assignment record")

        print(f"Assignment created successfully: {response.data[0]}")
        return {"success": True, "data": response.data[0]}

    except Exception as e:
        print(f"Assignment creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint removed - use production endpoints instead

# Employees API
@app.get("/api/employees/managed")
async def get_managed_employees(current_user = Depends(get_current_user)):
    """Get employees managed by the current user (manager/admin)"""
    try:
        manager_id = current_user.id
        print(f"Fetching managed employees for manager: {manager_id}")

        # Query user_reporting table to get all employees under this manager
        reporting_response = supabase_admin.table('user_reporting') \
            .select('employee_id') \
            .eq('manager_id', manager_id) \
            .execute()

        print(f"Reporting response data: {reporting_response.data}")

        if not reporting_response.data or len(reporting_response.data) == 0:
            print("No employees found for this manager")
            return {"employees": [], "total": 0}

        # Get employee IDs
        employee_ids = [record['employee_id'] for record in reporting_response.data]
        print(f"Employee IDs to fetch: {employee_ids}")

        # Handle empty employee_ids list
        if not employee_ids:
            print("No employee IDs to query")
            return {"employees": [], "total": 0}

        # Fetch employee details from user_miles table
        employees_response = supabase_admin.table('user_miles') \
            .select('id, auth_id, name, email, role, profile_picture') \
            .in_('auth_id', employee_ids) \
            .execute()

        employees = employees_response.data or []
        print(f"Found {len(employees)} employees")
        print(f"Sample employee data: {employees[0] if employees else 'None'}")

        # Sort by name
        employees.sort(key=lambda x: x.get('name', '').lower())

        return {
            "employees": employees,
            "total": len(employees)
        }

    except Exception as e:
        print(f"Get managed employees error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch managed employees: {str(e)}")


# Employee CRUD endpoints removed - these used non-existent 'employees' table
# Employee management is handled by employee_management router (uses user_miles + Supabase Auth)
# GET /api/employees/managed is kept (uses user_miles table correctly)

# Skills API Endpoints
@app.get("/api/skills/categories")
async def get_skill_categories(current_user: dict = Depends(get_current_user)):
    """Get all unique skill categories from the skills table"""
    try:
        # Query distinct categories from skills table
        response = supabase.table('skills').select('category').execute()

        if not response.data:
            return {"categories": []}

        # Extract unique categories
        categories = list(set(skill['category'] for skill in response.data if skill.get('category')))
        categories.sort()  # Sort alphabetically

        return {
            "categories": categories,
            "total": len(categories)
        }

    except Exception as e:
        print(f"Get skill categories error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch skill categories")

@app.get("/api/skills")
async def get_skills(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get skills, optionally filtered by category"""
    try:
        query = supabase.table('skills').select('*')

        # Filter by category if provided
        if category:
            query = query.eq('category', category)

        response = query.execute()
        skills = response.data or []

        # Apply search filter if provided
        if search:
            search_term = search.lower()
            skills = [
                skill for skill in skills
                if search_term in skill.get('name', '').lower() or
                   search_term in skill.get('category', '').lower()
            ]

        # Sort skills by name
        skills.sort(key=lambda x: x.get('name', '').lower())

        return {
            "skills": skills,
            "total": len(skills),
            "category": category
        }

    except Exception as e:
        print(f"Get skills error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch skills")

# Protected User Endpoints
@app.get("/api/user/profile")
async def user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "message": "User profile retrieved successfully",
        "user": get_current_user_info(current_user)
    }

# Example LangGraph endpoint (to be expanded)
@app.post("/api/langgraph/workflow")
async def run_workflow(data: dict, current_user: dict = Depends(get_current_user)):
    # Placeholder for LangGraph workflow
    return {"result": "Workflow executed", "data": data, "user": getattr(current_user, "email", "")}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
