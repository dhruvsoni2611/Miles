-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'employee' CHECK (role IN ('admin', 'employee')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies for role-based access
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text AND is_active = true);

CREATE POLICY "Admins can view all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id::text = auth.uid()::text
            AND u.role = 'admin'
            AND u.is_active = true
        )
    );

CREATE POLICY "Admins can manage users" ON users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users u
            WHERE u.id::text = auth.uid()::text
            AND u.role = 'admin'
            AND u.is_active = true
        )
    );

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();


-- Create storage bucket for AI generated images
INSERT INTO storage.buckets (id, name, public) 
VALUES ('ai-generated-images', 'ai-generated-images', true)
ON CONFLICT (id) DO NOTHING;

-- Create policy for AI generated images bucket
CREATE POLICY "AI generated images are publicly accessible" ON storage.objects
    FOR SELECT USING (bucket_id = 'ai-generated-images');

CREATE POLICY "Authenticated users can upload AI generated images" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'ai-generated-images' 
        AND auth.role() = 'authenticated'
    );

CREATE POLICY "Users can update their own AI generated images" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'ai-generated-images' 
        AND auth.role() = 'authenticated'
    );

CREATE POLICY "Users can delete their own AI generated images" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'ai-generated-images'
        AND auth.role() = 'authenticated'
    );

-- Insert default admin user (password: admin123)
-- Note: In production, change this password and use proper hashing
INSERT INTO users (email, name, password_hash, role, is_active)
VALUES (
    'admin@miles.com',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/5j7nMxgK5YHqjKxm', -- bcrypt hash for 'admin123'
    'admin',
    true
)
ON CONFLICT (email) DO NOTHING;

-- Insert sample employee user (password: employee123)
INSERT INTO users (email, name, password_hash, role, is_active)
VALUES (
    'employee@miles.com',
    'Sample Employee',
    '$2b$12$8K1p/5wX7VzqQ8fF0n3Oe.VfQzX9dLrX8Vx9nX5Yj1n6q7wXa9u2', -- bcrypt hash for 'employee123'
    'employee',
    true
)
ON CONFLICT (email) DO NOTHING;

