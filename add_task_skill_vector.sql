-- Migration to update tasks table schema to match new structure
-- Run this SQL script in your Supabase SQL editor

-- Rename existing columns to match new schema
ALTER TABLE public.tasks
RENAME COLUMN priority TO priority_score;

ALTER TABLE public.tasks
RENAME COLUMN difficulty_level TO difficulty_score;

ALTER TABLE public.tasks
RENAME COLUMN skill_vector TO skill_embedding;

-- Add new columns
ALTER TABLE public.tasks
ADD COLUMN IF NOT EXISTS rating_score INTEGER DEFAULT 0 CHECK (rating_score <= 5);

ALTER TABLE public.tasks
ADD COLUMN IF NOT EXISTS justified BOOLEAN DEFAULT false;

ALTER TABLE public.tasks
ADD COLUMN IF NOT EXISTS bonus BOOLEAN DEFAULT false;

-- Remove old columns that are no longer needed
ALTER TABLE public.tasks
DROP COLUMN IF EXISTS progress;

ALTER TABLE public.tasks
DROP COLUMN IF EXISTS notes;

-- Update constraints to match new column names
ALTER TABLE public.tasks
DROP CONSTRAINT IF EXISTS tasks_priority_check;

ALTER TABLE public.tasks
ADD CONSTRAINT tasks_priority_check CHECK (
  (
    (priority_score >= 1)
    AND (priority_score <= 5)
  )
);

ALTER TABLE public.tasks
DROP CONSTRAINT IF EXISTS tasks_difficulty_level_check;

ALTER TABLE public.tasks
ADD CONSTRAINT tasks_difficulty_level_check CHECK (
  (
    (difficulty_score >= 1)
    AND (difficulty_score <= 10)
  )
);

-- Add new constraints
ALTER TABLE public.tasks
ADD CONSTRAINT tasks_rating_score_check CHECK ((rating_score <= 5));

-- Update default values for existing records
UPDATE public.tasks
SET rating_score = 0
WHERE rating_score IS NULL;

UPDATE public.tasks
SET justified = false
WHERE justified IS NULL;

UPDATE public.tasks
SET bonus = false
WHERE bonus IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN public.tasks.skill_embedding IS 'AI embeddings for task skills used in task-employee matching';
COMMENT ON COLUMN public.tasks.rating_score IS 'Performance rating for completed tasks (1-5)';
COMMENT ON COLUMN public.tasks.justified IS 'Whether the task rating was justified';
COMMENT ON COLUMN public.tasks.bonus IS 'Whether the employee received a bonus for this task';