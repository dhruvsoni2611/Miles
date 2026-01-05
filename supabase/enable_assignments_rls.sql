-- =====================================================
-- ENABLE RLS FOR ASSIGNMENTS TABLE
-- =====================================================

-- Ensure assignments table exists (create if not exists)
CREATE TABLE IF NOT EXISTS public.assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES public.tasks(id),
  user_id UUID REFERENCES public.user_miles(auth_id),
  assigned_by UUID REFERENCES public.user_miles(auth_id),
  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  performance_rating INT CHECK (performance_rating BETWEEN 1 AND 5),
  actual_hours FLOAT,
  outcome_score FLOAT,
  notes TEXT
);

-- Enable Row Level Security
ALTER TABLE public.assignments ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "View assignments" ON public.assignments;
DROP POLICY IF EXISTS "Insert assignments" ON public.assignments;
DROP POLICY IF EXISTS "Update assignments" ON public.assignments;

-- Create comprehensive RLS policies
-- Allow anyone to view assignments (for reporting/analytics)
CREATE POLICY "View assignments"
ON public.assignments FOR SELECT
USING (true);

-- Allow service role (backend) to insert assignments
CREATE POLICY "Insert assignments"
ON public.assignments FOR INSERT
WITH CHECK (true);

-- Allow service role to update assignments (for completion tracking)
CREATE POLICY "Update assignments"
ON public.assignments FOR UPDATE
USING (true);

-- Optional: Allow authenticated users to see their own assignments
-- Uncomment if you want more restrictive policies
/*
CREATE POLICY "Users can view their own assignments"
ON public.assignments FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Managers can view assignments they created"
ON public.assignments FOR SELECT
USING (auth.uid() = assigned_by);
*/

-- Grant necessary permissions to service role
-- These should already be granted, but ensuring they exist
GRANT ALL ON public.assignments TO service_role;
GRANT ALL ON public.assignments TO authenticated;

-- Test: Try to select from assignments table
-- This should work if RLS is properly configured
SELECT COUNT(*) as assignment_count FROM public.assignments;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Assignments table RLS setup completed successfully!';
    RAISE NOTICE '📊 Current assignment count: %', (SELECT COUNT(*) FROM public.assignments);
END $$;

