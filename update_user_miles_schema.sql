-- Migration to update user_miles table to match new schema
-- Run this SQL script in your Supabase SQL editor

-- Add new id column as primary key
ALTER TABLE public.user_miles
ADD COLUMN IF NOT EXISTS id UUID NOT NULL DEFAULT gen_random_uuid();

-- Add workload column
ALTER TABLE public.user_miles
ADD COLUMN IF NOT EXISTS workload INTEGER NOT NULL DEFAULT 0;

-- Drop old primary key constraint if it exists on auth_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'user_miles_pkey'
        AND table_name = 'user_miles'
    ) THEN
        ALTER TABLE public.user_miles DROP CONSTRAINT user_miles_pkey;
    END IF;
END $$;

-- Add new primary key constraint on id
ALTER TABLE public.user_miles
ADD CONSTRAINT user_miles_pkey PRIMARY KEY (id);

-- Add unique constraint on auth_id if it doesn't exist
ALTER TABLE public.user_miles
ADD CONSTRAINT user_miles_auth_id_key UNIQUE (auth_id);

-- Add unique constraint on email if it doesn't exist
ALTER TABLE public.user_miles
ADD CONSTRAINT user_miles_email_key UNIQUE (email);

-- Update existing records to have default values
UPDATE public.user_miles
SET workload = 0
WHERE workload IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN public.user_miles.id IS 'Primary key - auto-generated UUID';
COMMENT ON COLUMN public.user_miles.auth_id IS 'Supabase auth user ID - must be unique';
COMMENT ON COLUMN public.user_miles.workload IS 'Current workload score (0-100, where 100 = fully loaded)';
COMMENT ON COLUMN public.user_miles.productivity_score IS 'Calculated productivity score based on experience and tenure';