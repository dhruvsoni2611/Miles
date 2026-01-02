# Miles Backend Setup Guide

## 🚀 Quick Setup (2 minutes)

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Quick Configuration
```bash
python quick_setup.py
```
This creates a `.env` file with placeholder values. Edit it with your Supabase credentials.

### 3. Apply Database Schema
1. Go to your Supabase project → SQL Editor
2. Copy and run the entire contents of `../supabase/schema.sql`
3. This creates all tables, policies, and relationships

### 4. Start Backend
```bash
python main.py
```
API will be available at `http://localhost:8000`

### 5. Test Everything
```bash
python troubleshoot.py
```
This checks your entire setup and tells you exactly what's wrong.

### 6. Test Frontend
- Start frontend: `cd frontend && npm run dev`
- Open http://localhost:5173
- Try creating a task - should work without "[object Object]" errors

## 🔧 Troubleshooting

If task creation fails with "[object Object]" error:

### Run Diagnostics
```bash
cd backend
python troubleshoot.py
```

This will check:
- ✅ Environment variables
- ✅ Python imports
- ✅ Supabase connection
- ✅ Backend server status
- ✅ API functionality

### Common Issues & Fixes

**❌ "[object Object]" Error:**
```bash
# 1. Check if .env exists and has real credentials
python quick_setup.py

# 2. Run diagnostics
python troubleshoot.py

# 3. Test API manually
python test_task_creation.py
```

**❌ "Failed to create task" Error:**
- Backend server not running: `python main.py`
- Database schema not applied: Run `schema.sql` in Supabase
- Wrong credentials: Check `.env` file values

**❌ Supabase Connection Failed:**
- Get credentials from: https://supabase.com/dashboard → Your Project → Settings → API
- Update `.env` file with real values
- Ensure database schema is applied

## 📋 Manual Setup (Detailed)

### Option A: Interactive Setup
```bash
python setup_supabase.py
```
Follow the prompts to configure everything.

### Option B: Manual .env Setup
Create `backend/.env`:
```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here
SECRET_KEY=your-jwt-secret-key-change-in-production
```

### 3. Set Up Database Schema
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the contents of `../supabase/schema.sql`
4. This creates all the necessary tables, policies, and relationships

### 4. Start the Backend
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 📋 API Endpoints

### Task Management
- `POST /api/tasks` - Create a new task
- `GET /api/tasks` - List tasks (filtered)
- `GET /api/tasks/{task_id}` - Get specific task
- `PUT /api/tasks/{task_id}` - Update task
- `DELETE /api/tasks/{task_id}` - Delete task

### Employee Management
- `GET /api/employees` - List employees
- `POST /api/employees` - Create employee
- `GET /api/employees/{id}` - Get employee
- `PUT /api/employees/{id}` - Update employee
- `DELETE /api/employees/{id}` - Delete employee

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User registration
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - User logout

## 🧪 Testing Task Creation

### Using cURL
```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "This is a test task",
    "priority": "high",
    "difficulty_level": 3,
    "status": "todo",
    "due_date": "2024-12-31T23:59:59.000Z"
  }'
```

### Using Python
```python
import requests

task_data = {
    "title": "Test Task",
    "description": "This is a test task",
    "priority": "high",
    "difficulty_level": 3,
    "status": "todo",
    "due_date": "2024-12-31T23:59:59.000Z"
}

response = requests.post("http://localhost:8000/api/tasks", json=task_data)
print(response.json())
```

## 🔧 Troubleshooting

### "Failed to create task" Error
1. Check your `.env` file has correct Supabase credentials
2. Ensure the database schema is applied in Supabase
3. Check backend logs for detailed error messages

### Database Connection Issues
1. Verify Supabase URL is correct
2. Check that service role key has proper permissions
3. Ensure RLS policies allow the operations

### Schema Issues
1. Make sure you've run the complete `schema.sql` file
2. Check that all tables were created successfully
3. Verify foreign key relationships are intact

## 📊 Database Schema Overview

The application uses these main tables:
- `user_miles` - User profiles
- `projects` - Project definitions
- `tasks` - Task management
- `assignments` - Task-user assignments
- `skills` - Available skills
- `user_skills` - User skill proficiency

## 🔐 Security Features

- Row Level Security (RLS) enabled on all tables
- JWT-based authentication
- Role-based access control (admin/manager/employee)
- Service role key for backend operations
- Proper input validation and sanitization

## 🎯 Task Creation Flow

1. **Frontend** sends task data via API
2. **Backend** validates input with Pydantic schemas
3. **Database** connection is verified
4. **Task data** is transformed (priority string → integer)
5. **Database insertion** creates the task record
6. **Response** includes computed fields like `is_overdue`
7. **Frontend** displays success message

No demo mode - everything works with real Supabase database! 🚀
