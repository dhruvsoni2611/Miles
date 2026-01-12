-- Create the assignments table for task assignment tracking
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  task_id UUID REFERENCES public.tasks(id),
  user_id UUID REFERENCES public.user_miles(id),
  assigned_by UUID REFERENCES public.user_miles(id),

  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,

  performance_rating INT CHECK (performance_rating BETWEEN 1 AND 5),
  actual_hours FLOAT,
  outcome_score FLOAT,
  notes TEXT
);

-- Enable Row Level Security
ALTER TABLE public.assignments ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY IF NOT EXISTS "View assignments"
ON public.assignments FOR SELECT
USING (true);

CREATE POLICY IF NOT EXISTS "Insert assignments"
ON public.assignments FOR INSERT
WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Update assignments"
ON public.assignments FOR UPDATE
USING (true);

-- Verify table was created
SELECT 'Assignments table created successfully!' as status;