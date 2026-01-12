-- Migration script to update assignments table to use user_miles.id references
-- Run this after updating the schema.sql file

-- First, add a temporary column to store the new IDs
ALTER TABLE public.assignments
ADD COLUMN temp_user_id UUID,
ADD COLUMN temp_assigned_by UUID;

-- Update the temporary columns with the correct user_miles.id values
UPDATE public.assignments
SET temp_user_id = um.id
FROM public.user_miles um
WHERE assignments.user_id::text = um.auth_id::text;

UPDATE public.assignments
SET temp_assigned_by = um.id
FROM public.user_miles um
WHERE assignments.assigned_by::text = um.auth_id::text;

-- Drop the old foreign key constraints
ALTER TABLE public.assignments
DROP CONSTRAINT IF EXISTS assignments_user_id_fkey,
DROP CONSTRAINT IF EXISTS assignments_assigned_by_fkey;

-- Update the columns with the new values
UPDATE public.assignments
SET user_id = temp_user_id,
    assigned_by = temp_assigned_by;

-- Drop the temporary columns
ALTER TABLE public.assignments
DROP COLUMN temp_user_id,
DROP COLUMN temp_assigned_by;

-- Add the new foreign key constraints
ALTER TABLE public.assignments
ADD CONSTRAINT assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_miles(id) ON DELETE CASCADE,
ADD CONSTRAINT assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.user_miles(id) ON DELETE CASCADE;

-- Verify the migration worked
SELECT
    a.id,
    a.task_id,
    um1.name as assigned_to_name,
    um2.name as assigned_by_name,
    a.assigned_at,
    a.completed_at
FROM public.assignments a
LEFT JOIN public.user_miles um1 ON a.user_id = um1.id
LEFT JOIN public.user_miles um2 ON a.assigned_by = um2.id
LIMIT 5;