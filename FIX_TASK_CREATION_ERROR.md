# 🚨 FIX: Task Creation Error "[object Object]"

## Problem
You're getting `Error: [object Object]` when trying to create tasks in the frontend.

## Root Cause
The backend doesn't have Supabase credentials configured, so it can't connect to the database.

## ✅ Quick Fix (2 minutes)

### 1. Configure Backend
```bash
cd backend
python quick_setup.py
```

### 2. Edit .env File
Open the newly created `.env` file and replace placeholder values with your real Supabase credentials:

```env
SUPABASE_URL=https://your-actual-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Your real key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Your real key
```

**Get credentials from:** https://supabase.com/dashboard → Your Project → Settings → API

### 3. Apply Database Schema
1. Go to Supabase SQL Editor
2. Copy entire contents of `supabase/schema.sql`
3. Run the SQL - this creates all tables

### 4. Start Backend
```bash
python main.py
```

### 5. Test Everything
```bash
python troubleshoot.py
```

If all checks pass ✅, your task creation will work!

## 🔧 Advanced Troubleshooting

### If Quick Fix Doesn't Work:

**Check Backend Logs:**
```bash
python main.py  # Look for error messages when starting
```

**Test API Directly:**
```bash
python test_task_creation.py
```

**Common Issues:**
- ❌ Wrong Supabase URL → Check project reference
- ❌ Invalid API keys → Regenerate in Supabase dashboard
- ❌ Schema not applied → Run SQL in Supabase editor
- ❌ Port 8000 in use → Kill other processes using the port

## 🎯 Expected Result

After fixing, you should see:
- ✅ Backend starts without errors
- ✅ `python troubleshoot.py` passes all checks
- ✅ Frontend task creation works
- ✅ Tasks appear in Supabase database

## 📞 Still Having Issues?

Run diagnostics and share the output:
```bash
cd backend
python troubleshoot.py
```

The output will tell us exactly what's wrong! 🔧

