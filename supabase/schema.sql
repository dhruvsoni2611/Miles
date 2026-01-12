-- =====================================================
-- 1. ENUMS
-- =====================================================
CREATE TYPE IF NOT EXISTS user_role AS ENUM ('employee', 'manager', 'admin');


-- =====================================================
-- 2. USER_MILES (formerly public.users)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.user_miles (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  auth_id UUID NOT NULL,
  email TEXT NOT NULL,
  name TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'employee'::user_role,
  profile_picture TEXT NULL,
  skill_vector JSONB NULL,
  productivity_score DOUBLE PRECISION NULL DEFAULT 0.0,
  created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT now(),
  experience_years JSONB NOT NULL DEFAULT '{}'::jsonb,
  tenure JSONB NOT NULL DEFAULT '{}'::jsonb,
  workload INTEGER NOT NULL DEFAULT 0,
  CONSTRAINT user_miles_pkey PRIMARY KEY (id),
  CONSTRAINT user_miles_auth_id_key UNIQUE (auth_id),
  CONSTRAINT user_miles_email_key UNIQUE (email),
  CONSTRAINT user_miles_auth_id_fkey FOREIGN KEY (auth_id) REFERENCES auth.users (id) ON DELETE CASCADE
) TABLESPACE pg_default;


-- =====================================================
-- 3. USER REPORTING (Manager ↔ Employee)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.user_reporting (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  employee_id UUID NOT NULL REFERENCES public.user_miles(auth_id) ON DELETE CASCADE,
  manager_id  UUID NOT NULL REFERENCES public.user_miles(auth_id) ON DELETE CASCADE,

  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  assigned_by UUID REFERENCES public.user_miles(auth_id),

  UNIQUE (employee_id),
  CHECK (employee_id <> manager_id)
);


-- =====================================================
-- 4. PROJECTS
-- =====================================================
CREATE TABLE IF NOT EXISTS public.projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  created_by UUID REFERENCES public.user_miles(auth_id),
  deadline DATE,
  status TEXT DEFAULT 'active'
    CHECK (status IN ('active', 'archived', 'paused')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);


-- =====================================================
-- 5. TASKS
-- =====================================================
CREATE TABLE IF NOT EXISTS public.tasks (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  project_id UUID NULL,
  title TEXT NOT NULL,
  description TEXT NULL,
  priority_score INTEGER NULL DEFAULT 1,
  difficulty_score INTEGER NULL DEFAULT 1,
  required_skills JSONB NULL,
  status TEXT NULL DEFAULT 'todo'::text,
  assigned_to UUID NULL,
  created_by UUID NULL,
  due_date TIMESTAMP WITH TIME ZONE NULL,
  created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT now(),
  rating_score INTEGER NULL DEFAULT 0,
  justified BOOLEAN NULL DEFAULT false,
  bonus BOOLEAN NULL DEFAULT false,
  skill_embedding JSONB NULL,
  CONSTRAINT tasks_pkey PRIMARY KEY (id),
  CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES projects (id),
  CONSTRAINT tasks_difficulty_level_check CHECK (
    (
      (difficulty_score >= 1)
      AND (difficulty_score <= 10)
    )
  ),
  CONSTRAINT tasks_priority_check CHECK (
    (
      (priority_score >= 1)
      AND (priority_score <= 5)
    )
  ),
  CONSTRAINT tasks_rating_score_check CHECK ((rating_score <= 5)),
  CONSTRAINT tasks_status_check CHECK (
    (
      status = ANY (
        ARRAY[
          'todo'::text,
          'in_progress'::text,
          'review'::text,
          'done'::text
        ]
      )
    )
  )
) TABLESPACE pg_default;


-- =====================================================
-- 6. ASSIGNMENTS (RL MEMORY)
-- =====================================================
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

-- Migration: Update existing assignments to use user_miles.id instead of auth_id
-- This ensures existing data works with the new foreign key references
DO $$
BEGIN
  -- Update user_id column to reference user_miles.id
  UPDATE public.assignments
  SET user_id = um.id
  FROM public.user_miles um
  WHERE assignments.user_id = um.auth_id::text;

  -- Update assigned_by column to reference user_miles.id
  UPDATE public.assignments
  SET assigned_by = um.id
  FROM public.user_miles um
  WHERE assignments.assigned_by = um.auth_id::text;
EXCEPTION
  WHEN others THEN
    -- Log the error but don't fail the migration
    RAISE NOTICE 'Migration of assignments table completed with warnings: %', SQLERRM;
END $$;


-- =====================================================
-- 7. SKILLS
-- =====================================================
CREATE TABLE IF NOT EXISTS public.skills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  category TEXT
);


-- =====================================================
-- 8. USER SKILLS
-- =====================================================
CREATE TABLE IF NOT EXISTS public.user_skills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.user_miles(auth_id) ON DELETE CASCADE,
  skill_id UUID REFERENCES public.skills(id) ON DELETE CASCADE,

  proficiency INT CHECK (proficiency BETWEEN 1 AND 10),
  experience_level INT,

  last_updated TIMESTAMPTZ DEFAULT NOW()
);


-- =====================================================
-- 9. TASK SKILL REQUIREMENTS
-- =====================================================
CREATE TABLE IF NOT EXISTS public.task_skill_requirements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE,
  skill_id UUID REFERENCES public.skills(id) ON DELETE CASCADE,

  required_level INT CHECK (required_level BETWEEN 1 AND 10),
  weight FLOAT DEFAULT 1.0
);


-- =====================================================
-- 10. UPDATED_AT TRIGGERS
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_miles_updated_at
BEFORE UPDATE ON public.user_miles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
BEFORE UPDATE ON public.tasks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- 11. AUTO REPORTING TRIGGER
-- =====================================================
CREATE OR REPLACE FUNCTION auto_assign_reporting()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.role = 'employee' THEN
    INSERT INTO public.user_reporting (
      employee_id,
      manager_id,
      assigned_by
    )
    SELECT
      NEW.auth_id,
      auth.uid(),
      auth.uid()
    FROM public.user_miles
    WHERE auth_id = auth.uid()
      AND role = 'manager';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER auto_assign_employee_to_manager
AFTER INSERT ON public.user_miles
FOR EACH ROW
EXECUTE FUNCTION auto_assign_reporting();


-- =====================================================
-- 12. ENABLE RLS
-- =====================================================
ALTER TABLE public.user_miles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_reporting ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_skill_requirements ENABLE ROW LEVEL SECURITY;


-- =====================================================
-- 13. RLS POLICIES
-- =====================================================

-- USER_MILES
CREATE POLICY "View public profiles"
ON public.user_miles FOR SELECT
USING (true);

CREATE POLICY "Update own profile"
ON public.user_miles FOR UPDATE
USING (auth.uid() = auth_id);

CREATE POLICY "Managers create employees"
ON public.user_miles FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.user_miles
    WHERE auth_id = auth.uid()
      AND role IN ('manager', 'admin')
  )
);

-- PROJECTS
CREATE POLICY "View projects"
ON public.projects FOR SELECT
USING (true);

CREATE POLICY "Managers manage projects"
ON public.projects FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.user_miles
    WHERE auth_id = auth.uid()
      AND role IN ('manager', 'admin')
  )
);

-- TASKS
CREATE POLICY "View tasks"
ON public.tasks FOR SELECT
USING (true);

CREATE POLICY "Managers manage tasks"
ON public.tasks FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.user_miles
    WHERE auth_id = auth.uid()
      AND role IN ('manager', 'admin')
  )
);

-- ASSIGNMENTS & SKILLS
CREATE POLICY IF NOT EXISTS "View assignments"
ON public.assignments FOR SELECT
USING (true);

CREATE POLICY IF NOT EXISTS "Insert assignments"
ON public.assignments FOR INSERT
WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "Update assignments"
ON public.assignments FOR UPDATE
USING (true);

CREATE POLICY "View skills"
ON public.skills FOR SELECT
USING (true);

CREATE POLICY "View user skills"
ON public.user_skills FOR SELECT
USING (true);

-- REPORTING
CREATE POLICY "View reporting"
ON public.user_reporting FOR SELECT
USING (
  employee_id = auth.uid()
  OR manager_id = auth.uid()
);

CREATE POLICY "Admins manage reporting"
ON public.user_reporting FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.user_miles
    WHERE auth_id = auth.uid()
      AND role = 'admin'
  )
);


-- =====================================================
-- 14. STORAGE (UNCHANGED)
-- =====================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('ai-generated-images', 'ai-generated-images', true)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Storage Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'ai-generated-images');

CREATE POLICY "Storage Insert"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'ai-generated-images'
  AND auth.role() = 'authenticated'
);

CREATE POLICY "Storage Update"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'ai-generated-images'
  AND auth.role() = 'authenticated'
);

CREATE POLICY "Storage Delete"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'ai-generated-images'
  AND auth.role() = 'authenticated'
);