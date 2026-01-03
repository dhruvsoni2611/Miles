-- Add progress field to tasks table
-- Run this in your Supabase SQL Editor

ALTER TABLE public.tasks
ADD COLUMN IF NOT EXISTS progress INT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100);

-- Verify the column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'tasks' AND column_name = 'progress';

