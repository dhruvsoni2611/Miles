# Miles Backend Setup

## Environment Variables

The `.env` file should be configured with your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here

# Optional: Custom JWT secret (falls back to SUPABASE_JWT_SECRET)
SECRET_KEY=your-jwt-secret-key-change-in-production
```

## Database Setup

The system now uses **Supabase Auth** (built-in authentication) instead of a custom table. This provides:

- Secure user registration and login
- JWT token management
- Password reset functionality
- User metadata for roles

### User Roles

User roles are stored in the `user_metadata` field:
- `role: "admin"` - Administrator access
- `role: "employee"` - Employee access (default)

## Testing Your Setup

### 1. Check Connection
```bash
curl http://localhost:8000/api/test/connection
```

### 2. View All Users (Admin)
```bash
curl http://localhost:8000/api/test/users
```

### 3. Test Authentication
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

## Running the Backend

```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Run the development server
python main.py
```

## API Endpoints

### Authentication
- **POST** `/api/auth/login` - Login with email/password
- **POST** `/api/auth/signup` - Register new user
- **POST** `/api/auth/logout` - Logout
- **GET** `/api/auth/me` - Get current user info
- **GET** `/api/auth/verify` - Verify token validity

### Dashboards (Protected)
- **GET** `/api/admin/dashboard` - Admin dashboard (admin role required)
- **GET** `/api/employee/dashboard` - Employee dashboard (employee role required)

### Testing/Debugging
- **GET** `/api/test/connection` - Check Supabase connection
- **GET** `/api/test/users` - View all users (requires service role)
- **POST** `/api/test/login` - Test login

### Health Checks
- **GET** `/` - Basic health check
- **GET** `/api/health` - Detailed health check

The API will be available at `http://localhost:8000`

## Supabase Setup

1. **Create a Supabase project**
2. **Enable Email Auth** in Authentication settings
3. **Configure SMTP** for email confirmations (optional)
4. **Copy credentials** to your `.env` file

## User Management

### Creating Admin Users
After signup, you can update user roles using the Supabase dashboard:
1. Go to Authentication > Users
2. Edit user metadata: `{"role": "admin", "name": "User Name"}`

### Sample Users
Create these users in Supabase Auth:
- **Admin**: admin@example.com / admin123 (role: admin)
- **Employee**: employee@example.com / employee123 (role: employee)

## Frontend Integration

The frontend uses Supabase Auth directly:
- Login with email/password
- Automatic session management
- Real-time auth state updates
- Secure token handling

Make sure your `frontend/.env.local` has:
```env
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```
