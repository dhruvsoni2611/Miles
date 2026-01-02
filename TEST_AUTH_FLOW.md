# 🔐 TESTING AUTHENTICATION FLOW

## Problem
Getting "Your session has expired. Please login again." when trying to create tasks.

## Solution
This is **correct behavior** - authentication is working! You just need to login first.

## ✅ Complete Testing Flow

### 1. Start Both Services
```bash
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### 2. Login First
1. **Open Frontend:** http://localhost:5173
2. **Go to Login Page:** Click login or navigate to `/login`
3. **Login Options:**

   **Option A: Use Supabase Auth UI**
   - Frontend has Supabase integration
   - Use the built-in login form

   **Option B: Use Backend API**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "password123"}'
   ```

### 3. Create Test User (if needed)
If you don't have users, create one in Supabase:

```sql
-- Run in Supabase SQL Editor
INSERT INTO user_miles (id, email, name, role)
VALUES (
  'test-user-123',
  'test@example.com',
  'Test User',
  'admin'
);
```

### 4. Test Task Creation
After successful login:
1. **Go to Dashboard**
2. **Click "Add Task"**
3. **Fill form and submit**
4. ✅ **Task should be created successfully!**

## 🔧 Environment Setup

### Backend .env
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret
SECRET_KEY=your-secret-key
```

### Frontend .env
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

## 🎯 Expected Behavior

### ❌ Before Login
- Clicking "Add Task" → "Please login to create tasks"
- Task creation → "Your session has expired. Please login again."

### ✅ After Login
- Clicking "Add Task" → Modal opens
- Task creation → Success! Task stored with real user ID

## 🔍 Debugging

### Check Authentication Status
```bash
# Test login endpoint
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Should return: {"access_token": "...", "user": {...}}
```

### Check Database
```sql
-- Check if user exists
SELECT * FROM user_miles WHERE email = 'test@example.com';

-- Check created tasks
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 5;
```

## 🚀 Quick Test

1. **Login** (creates session)
2. **Create task** (uses session token)
3. **Check database** (task has real user ID in created_by)

**The "session expired" message is good - it means authentication is working!** 🎉
