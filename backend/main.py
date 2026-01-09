from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
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
    try:
        # Fallback for direct execution
        import sys
        import os
        backend_dir = os.path.dirname(__file__)
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from routers.employee_management import router as employee_router
    except ImportError:
        # Last resort - create empty router to prevent crashes
        from fastapi import APIRouter
        employee_router = APIRouter()
        print("Warning: Could not import employee_management router")

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

# Test CORS endpoint
@app.get("/api/test/cors")
async def test_cors():
    return {"message": "CORS is working!", "origin": "allowed"}

# Test endpoint to check Supabase Auth users
@app.get("/api/test/users")
async def test_users():
    """Test endpoint to check Supabase Auth users (admin only)"""
    try:
        # This endpoint should be protected, but for testing we'll allow it
        users_response = supabase_admin.auth.admin.list_users()
        users = []

        for user in users_response:
            users.append({
                "id": user.id,
                "email": user.email,
                "role": user.user_metadata.get('role', 'employee') if user.user_metadata else 'employee',
                "name": user.user_metadata.get('name', '') if user.user_metadata else '',
                "created_at": user.created_at,
                "email_confirmed_at": user.email_confirmed_at
            })

        return {
            "success": True,
            "users": users,
            "count": len(users)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Test endpoint to check Supabase connection
@app.get("/api/test/connection")
async def test_connection():
    """Test endpoint to check Supabase connection"""
    try:
        # Try to get user count from auth
        users_response = supabase_admin.auth.admin.list_users()
        user_count = len(users_response) if users_response else 0

        return {
            "success": True,
            "message": "Supabase connection successful",
            "user_count": user_count,
            "env_vars": {
                "supabase_url": bool(SUPABASE_URL),
                "supabase_anon_key": bool(SUPABASE_ANON_KEY),
                "supabase_service_role_key": bool(SUPABASE_SERVICE_ROLE_KEY)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "env_vars": {
                "supabase_url": bool(SUPABASE_URL),
                "supabase_anon_key": bool(SUPABASE_ANON_KEY),
                "supabase_service_role_key": bool(SUPABASE_SERVICE_ROLE_KEY)
            }
        }

# Test login endpoint
@app.post("/api/test/login")
async def test_login(login_data: LoginRequest):
    """Test login endpoint to check Supabase Auth"""
    try:
        # Use the actual login endpoint
        response = await login(login_data)
        return {
            "success": True,
            "message": "Login successful",
            "data": response.dict()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Login failed"
        }

# Test endpoint to check available tables
@app.get("/api/test/tables")
async def test_tables():
    """Test endpoint to check what tables exist in the database"""
    try:
        # This is a simple way to check if tables exist by trying to query them
        tables_to_check = ['taskadmin', 'users', 'user_miles']
        results = {}

        for table_name in tables_to_check:
            try:
                response = supabase.table(table_name).select('*').limit(1).execute()
                results[table_name] = {
                    "exists": True,
                    "sample_data": response.data[0] if response.data else None,
                    "record_count": len(response.data) if response.data else 0
                }
            except Exception as e:
                results[table_name] = {
                    "exists": False,
                    "error": str(e)
                }

        return {
            "success": True,
            "tables_checked": tables_to_check,
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Endpoint to check table schema and help setup
@app.get("/api/test/schema")
async def check_table_schema():
    """Check the schema/columns of task_admins table and provide setup guidance"""
    try:
        # Try to get a sample record to see the structure
        response = supabase.table('task_admins').select('*').limit(1).execute()

        if response.data and len(response.data) > 0:
            sample_record = response.data[0]
            columns = list(sample_record.keys())

            # Analyze the structure
            analysis = {
                "has_username": "username" in columns,
                "has_password": "password" in columns or "password_hash" in columns,
                "has_role": "role" in columns,
                "has_is_active": "is_active" in columns,
                "has_email": "email" in columns,
                "has_name": "name" in columns
            }

            return {
                "success": True,
                "columns": columns,
                "sample_data": sample_record,
                "structure_analysis": analysis,
                "recommendations": get_recommendations(analysis)
            }
        else:
            # Table is empty, try to determine schema by attempting inserts
            return await analyze_empty_table()

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestions": [
                "Check if task_admins table exists in your Supabase database",
                "Verify your SUPABASE_URL and SUPABASE_ANON_KEY in .env file",
                "Ensure you have proper permissions to access the table"
            ]
        }

async def analyze_empty_table():
    """Analyze an empty table to determine its structure"""
    test_cases = [
        {"username": "test_user", "password": "test123"},
        {"username": "test_user", "password": "test123", "role": "admin"},
        {"username": "test_user", "password": "test123", "role": "admin", "is_active": True},
        {"username": "test_user", "password": "test123", "role": "admin", "is_active": True, "email": "test@example.com"},
        {"username": "test_user", "password": "test123", "role": "admin", "is_active": True, "email": "test@example.com", "name": "Test User"}
    ]

    working_fields = set()
    failed_fields = set()

    for test_data in test_cases:
        try:
            # Try to insert
            response = supabase.table('task_admins').insert(test_data).execute()
            if response.data:
                # Success! Delete the test record
                supabase.table('task_admins').delete().eq('username', 'test_user').execute()
                working_fields.update(test_data.keys())
            break
        except Exception as e:
            error_str = str(e)
            # Check which fields are missing
            for field in test_data.keys():
                if f"'{field}'" in error_str and "column" in error_str:
                    failed_fields.add(field)

    # Determine which fields are supported
    supported_fields = working_fields - failed_fields

    return {
        "success": True,
        "message": "Table exists but is empty",
        "supported_fields": list(supported_fields),
        "unsupported_fields": list(failed_fields),
        "recommendations": [
            f"Your table supports these fields: {', '.join(supported_fields)}",
            "Add at least one user with username and password to test authentication",
            "Consider adding 'role' field for admin/employee access control"
        ]
    }

def get_recommendations(analysis):
    """Get recommendations based on table structure analysis"""
    recommendations = []

    if not analysis["has_username"]:
        recommendations.append("Add 'username' column for user identification")
    if not analysis["has_password"] and not analysis["has_password"]:
        recommendations.append("Add 'password' or 'password_hash' column for authentication")
    if not analysis["has_role"]:
        recommendations.append("Add 'role' column for access control (admin/employee)")
    if not analysis["has_is_active"]:
        recommendations.append("Add 'is_active' column for user status management")

    if len(recommendations) == 0:
        recommendations.append("Table structure looks good for authentication!")

    return recommendations

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
        profile_id = current_user['id']

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

# Tasks API
@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task_data: TaskBase, current_user = Depends(get_current_user)):
    """Create a new task"""
    try:
        # Get current user ID
        user_id = current_user.id

        # Validate required skills if provided
        if task_data.required_skills and len(task_data.required_skills) > 0:
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

        # Prepare task data for insertion
        task_dict = task_data.dict()
        task_dict['created_by'] = user_id
        task_dict['assigned_to'] = task_dict.get('assigned_to') or user_id

        # Convert date objects to ISO format for Supabase
        if task_dict.get('due_date') and isinstance(task_dict['due_date'], datetime):
            task_dict['due_date'] = task_dict['due_date'].isoformat()

        # Insert task into database
        response = supabase_admin.table('tasks').insert(task_dict).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create task")

        created_task = response.data[0]
        return TaskResponse(**created_task)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Create task error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

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
        existing_response = supabase_admin.table('tasks').select('id').or_(f'created_by.eq.{user_id},assigned_to.eq.{user_id}').eq('id', task_id).execute()

        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="Task not found or access denied")

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

        # Assignment creation is now handled by frontend via separate API call
        # This allows for better error handling and separation of concerns

        return TaskResponse(**updated_task)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Update task error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

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

# Test assignment creation directly
@app.post("/api/test-direct-assignment")
async def test_direct_assignment():
    """Test assignment creation directly"""
    try:
        from routers.employee_management import get_supabase_admin
        supabase_client = get_supabase_admin()

        # Create a test assignment record
        test_assignment = {
            'task_id': '550e8400-e29b-41d4-a716-446655440000',  # dummy UUID
            'user_id': '550e8400-e29b-41d4-a716-446655440001',  # dummy UUID
            'assigned_by': '550e8400-e29b-41d4-a716-446655440002', # dummy UUID
            'assigned_at': '2024-01-01T12:00:00.000Z'
        }

        print(f"DEBUG: Testing direct assignment creation: {test_assignment}")
        response = supabase_client.table("assignments").insert(test_assignment).execute()
        print(f"DEBUG: Direct assignment response: {response}")

        return {
            "success": True,
            "test_assignment": test_assignment,
            "response": response.data,
            "message": "Direct assignment creation test completed"
        }

    except Exception as e:
        print(f"Direct assignment test error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# Simple test assignment creation
@app.post("/api/test-create-assignment")
async def test_create_assignment():
    """Test assignment creation with known good data"""
    try:
        from routers.employee_management import get_supabase_admin
        supabase_client = get_supabase_admin()

        # Create assignment with hardcoded test data
        test_assignment = {
            'task_id': '550e8400-e29b-41d4-a716-446655440000',  # dummy task ID
            'user_id': '35ece19f-d073-46d5-9d19-a26424895a74',   # real user ID (from your data)
            'assigned_by': '58d91fe2-1401-46fd-b183-a2a118997fc1', # real user ID
            'assigned_at': '2024-01-01T12:00:00.000Z'
        }

        print(f"SIMPLE TEST: Creating assignment: {test_assignment}")
        response = supabase_client.table("assignments").insert(test_assignment).execute()
        print(f"SIMPLE TEST: Response: {response}")
        print(f"SIMPLE TEST: Response data: {response.data}")

        return {
            "success": True,
            "test_assignment": test_assignment,
            "response": response.data,
            "message": "Simple assignment creation test completed"
        }

    except Exception as e:
        print(f"SIMPLE TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

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

# Check assignments table data
@app.get("/api/check-assignments")
async def check_assignments():
    """Check current state of assignments table"""
    try:
        from routers.employee_management import get_supabase_admin
        supabase_client = get_supabase_admin()

        # Get all assignments
        assignments = supabase_client.table("assignments").select("*").limit(20).execute()

        # Get tasks with assignments
        tasks_with_assignments = supabase_client.table("tasks").select("*").not_("assigned_to", "is", None).limit(10).execute()

        return {
            "success": True,
            "assignments_count": len(assignments.data) if assignments.data else 0,
            "assignments": assignments.data,
            "tasks_with_assignments_count": len(tasks_with_assignments.data) if tasks_with_assignments.data else 0,
            "tasks_with_assignments": [
                {
                    "id": task["id"],
                    "title": task["title"],
                    "assigned_to": task["assigned_to"],
                    "created_by": task["created_by"]
                } for task in (tasks_with_assignments.data or [])
            ]
        }

    except Exception as e:
        print(f"Check assignments error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

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
            .select('auth_id, name, email, role, profile_picture') \
            .in_('auth_id', employee_ids) \
            .execute()

        employees = employees_response.data or []
        print(f"Found {len(employees)} employees")

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


@app.get("/api/employees")
async def get_employees(
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get employees for the current admin user with optional filters"""
    try:
        profile_id = current_user['id']
        query = supabase.table('employees').select('*').eq('profile_id', profile_id)

        # Apply filters
        if status:
            query = query.eq('status', status)
        if department:
            query = query.ilike('department', f'%{department}%')

        response = query.execute()
        employees = response.data or []

        # Apply search filter if provided
        if search:
            search_term = search.lower()
            employees = [
                emp for emp in employees
                if search_term in emp.get('name', '').lower() or
                   search_term in emp.get('email', '').lower() or
                   search_term in emp.get('employee_code', '').lower()
            ]

        # Sort in descending order (most recent first)
        employees.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return {"employees": employees, "total": len(employees)}

    except Exception as e:
        print(f"Get employees error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch employees")

@app.post("/api/employees", response_model=EmployeeResponse)
async def create_employee(employee_data: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    """Create a new employee"""
    try:
        profile_id = current_user['id']

        # Generate employee code (EMP001, EMP002, etc.)
        employees_response = supabase.table('employees').select('employee_code').eq('profile_id', profile_id).execute()
        existing_codes = [emp['employee_code'] for emp in (employees_response.data or [])]

        # Find next available code
        code_number = 1
        while f'EMP{code_number:03d}' in existing_codes:
            code_number += 1

        employee_code = f'EMP{code_number:03d}'

        employee_dict = employee_data.dict()
        employee_dict['profile_id'] = profile_id
        employee_dict['employee_code'] = employee_code
        employee_dict['status'] = 'active'
        employee_dict['is_active'] = True

        response = supabase.table('employees').insert(employee_dict).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create employee")

        created_employee = response.data[0]
        return EmployeeResponse(**created_employee)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Create employee error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create employee")

@app.get("/api/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific employee"""
    try:
        profile_id = current_user['id']

        response = supabase.table('employees').select('*').eq('id', employee_id).eq('profile_id', profile_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Employee not found")

        return EmployeeResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        print(f"Get employee error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch employee")

@app.put("/api/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: str, employee_data: EmployeeUpdate, current_user: dict = Depends(get_current_user)):
    """Update an employee"""
    try:
        profile_id = current_user['id']

        # Check if employee exists and belongs to user
        existing_response = supabase.table('employees').select('id').eq('id', employee_id).eq('profile_id', profile_id).execute()

        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Update employee
        update_dict = employee_data.dict(exclude_unset=True)
        update_dict['updated_at'] = datetime.utcnow().isoformat()

        response = supabase.table('employees').update(update_dict).eq('id', employee_id).eq('profile_id', profile_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to update employee")

        updated_employee = response.data[0]
        return EmployeeResponse(**updated_employee)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Update employee error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update employee")

@app.delete("/api/employees/{employee_id}")
async def delete_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an employee"""
    try:
        profile_id = current_user['id']

        # Check if employee exists and belongs to user
        existing_response = supabase.table('employees').select('id').eq('id', employee_id).eq('profile_id', profile_id).execute()

        if not existing_response.data or len(existing_response.data) == 0:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Delete employee
        response = supabase.table('employees').delete().eq('id', employee_id).eq('profile_id', profile_id).execute()

        return {"message": "Employee deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete employee error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete employee")

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
    return {"result": "Workflow executed", "data": data, "user": current_user["email"]}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
