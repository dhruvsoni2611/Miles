from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import jwt
import bcrypt
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "admin" or "employee"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool

# Mock Database (Replace with actual Supabase queries)
MOCK_USERS = {
    "admin@miles.com": {
        "id": "admin-uuid",
        "email": "admin@miles.com",
        "name": "System Administrator",
        "password_hash": b"$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/5j7nMxgK5YHqjKxm",  # admin123
        "role": "admin",
        "is_active": True
    },
    "employee@miles.com": {
        "id": "employee-uuid",
        "email": "employee@miles.com",
        "name": "Sample Employee",
        "password_hash": b"$2b$12$8K1p/5wX7VzqQ8fF0n3Oe.VfQzX9dLrX8Vx9nX5Yj1n6q7wXa9u2",  # employee123
        "role": "employee",
        "is_active": True
    }
}

# Authentication Functions
def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(email: str, password: str, expected_role: str):
    """Authenticate user with email, password and role"""
    user = MOCK_USERS.get(email)
    if not user:
        return False
    if not user["is_active"]:
        return False
    if user["role"] != expected_role:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

def get_current_user(token: str = Depends(HTTPBearer())):
    """Get current authenticated user from JWT token"""
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = MOCK_USERS.get(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Security scheme
security = HTTPBearer()

# Initialize FastAPI app
app = FastAPI(
    title="Miles API",
    description="AI-powered backend with LangGraph",
    version="1.0.0"
)

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

# Authentication Endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login endpoint for both admin and employee users"""
    user = authenticate_user(login_data.email, login_data.password, login_data.role)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or role",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time (mock)
    user["last_login"] = datetime.utcnow()

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    # Return token and user info (without password hash)
    user_response = {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "is_active": user["is_active"]
    }

    return TokenResponse(access_token=access_token, user=user_response)

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint"""
    # In a real implementation, you might want to blacklist the token
    # For now, we'll just return success
    return {"message": "Successfully logged out"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        is_active=current_user["is_active"]
    )

@app.get("/api/auth/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify if the current token is valid"""
    return {"valid": True, "user": current_user}

# Protected Admin Endpoints
@app.get("/api/admin/dashboard")
async def admin_dashboard(current_user: dict = Depends(get_current_user)):
    """Admin-only dashboard data"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "message": "Welcome to Admin Dashboard",
        "total_users": len(MOCK_USERS),
        "active_users": len([u for u in MOCK_USERS.values() if u["is_active"]]),
        "user": current_user
    }

# Protected Employee Endpoints
@app.get("/api/employee/dashboard")
async def employee_dashboard(current_user: dict = Depends(get_current_user)):
    """Employee dashboard data"""
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Employee access required")

    return {
        "message": "Welcome to Employee Dashboard",
        "user": current_user,
        "features": ["View Profile", "Update Settings", "Access Workflows"]
    }

# Example LangGraph endpoint (to be expanded)
@app.post("/api/langgraph/workflow")
async def run_workflow(data: dict, current_user: dict = Depends(get_current_user)):
    # Placeholder for LangGraph workflow
    return {"result": "Workflow executed", "data": data, "user": current_user["email"]}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
