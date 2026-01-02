# 🔐 Authentication Setup Guide

## Problem
Getting "No active session" error when trying to create tasks.

## Root Cause
The backend now requires authentication, but the user needs to be properly logged in with a valid session.

## ✅ Solution Steps

### 1. Backend Environment Setup
Create a `.env` file in the backend directory with your Supabase credentials:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here
SECRET_KEY=your-jwt-secret-key-change-in-production
```

### 2. Frontend Environment Setup
Create a `.env` file in the frontend directory:

```env
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
VITE_API_URL=http://localhost:8000
```

### 3. Database Setup
1. Go to Supabase SQL Editor
2. Run the entire contents of `supabase/schema.sql`
3. This creates the `user_miles` table and task-related tables

### 4. Create Test User (Optional)
If you don't have users in your database, you can create one manually in Supabase SQL Editor:

```sql
INSERT INTO user_miles (id, email, name, role)
VALUES (
  'test-user-id-123',
  'admin@example.com',
  'Test Admin',
  'admin'
);
```

### 5. Testing Flow

#### Start Services
```bash
# Terminal 1: Start Backend
cd backend && python main.py

# Terminal 2: Start Frontend
cd frontend && npm run dev
```

#### Authentication Flow
1. **Open Frontend:** http://localhost:5173
2. **Go to Login Page:** Click login or navigate to `/login`
3. **Login with Supabase Auth:**
   - Use Supabase Auth UI
   - Or use the custom login form with test credentials
4. **Create Session:** Successful login creates JWT token
5. **Create Task:** Now you can create tasks with proper authentication

#### Expected Behavior
- ✅ **Before Login:** Task creation shows "Please login to create tasks"
- ✅ **After Login:** Task creation works with real user authentication
- ✅ **Token Expiry:** Auto-refreshes or redirects to login
- ✅ **Database:** Tasks stored with real user ID in `created_by` field

## 🔧 Troubleshooting

### "No active session" Error
- **Cause:** User not logged in or session expired
- **Fix:** Login through the frontend authentication flow

### "Authentication failed" Error
- **Cause:** Invalid or missing JWT token
- **Fix:** Check that `.env` files have correct Supabase keys

### "Database connection failed" Error
- **Cause:** Supabase credentials wrong or missing
- **Fix:** Verify `.env` file has correct values

### "Task creation failed: 401 Unauthorized"
- **Cause:** JWT token invalid or expired
- **Fix:** Login again to refresh the session

## 🎯 Key Points

- **Backend requires authentication** for all task operations
- **Frontend auto-handles** token refresh and session management
- **Database stores** real user IDs in `created_by` field
- **Session management** handles token expiry automatically

## 🚀 Ready to Test

Once you have:
- ✅ `.env` files with Supabase credentials
- ✅ Database schema applied
- ✅ Backend and frontend running
- ✅ User logged in with valid session

**Task creation should work perfectly with proper authentication!** 🎉
