# 👤 CREATE TEST USER IN SUPABASE

## Problem
Login failing because no users exist in Supabase.

## Solution
Create a test user through Supabase Auth UI or SQL.

## ✅ Method 1: Supabase Auth UI (Recommended)

1. **Go to Supabase Dashboard:** https://supabase.com/dashboard
2. **Select your project**
3. **Go to Authentication → Users**
4. **Click "Add user"**
5. **Fill details:**
   - Email: `admin@example.com`
   - Password: `password123`
   - Auto-confirm: ✅ (check the box)
6. **Click "Create user"**

## ✅ Method 2: SQL Insert (Alternative)

If you want to create a user manually:

```sql
-- Run this in Supabase SQL Editor
-- This creates a user record (but they still need to register through Auth)

-- First, create the user through Supabase Auth UI (Method 1 above)
-- Then add their profile to user_miles table:

INSERT INTO user_miles (id, email, name, role)
VALUES (
  'the-actual-user-id-from-auth', -- Get this from Supabase Auth users list
  'admin@example.com',
  'Admin User',
  'admin'
);
```

## 🔍 Find User ID

After creating user in Supabase Auth:
1. Go to **Authentication → Users**
2. Click on the user
3. Copy the **User ID** (UUID)
4. Use that ID in the SQL insert above

## 🧪 Test Login

After creating the user:

1. **Start services:**
   ```bash
   cd backend && python main.py
   cd frontend && npm run dev
   ```

2. **Login:**
   - Email: `admin@example.com`
   - Password: `password123`

3. **Create task** - should work now!

## 📊 What This Does

- ✅ Creates authenticated user in Supabase Auth
- ✅ Links user profile in `user_miles` table
- ✅ Enables proper JWT token generation
- ✅ Allows `ensureValidSession()` to work
- ✅ Tasks get created with real user ID

## 🚨 Important

**The user MUST exist in Supabase Auth first** before you can login. The SQL insert only creates the profile data - the authentication happens through Supabase Auth.

**Create the user through the Supabase dashboard Auth → Users section first!** 🎯

