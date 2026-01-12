-- Create RL Miles table for reinforcement learning feedback
-- Following the exact schema provided
CREATE TABLE IF NOT EXISTS public.rl_miles (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  r_completion BOOLEAN NOT NULL DEFAULT false,
  r_ontime BOOLEAN NOT NULL DEFAULT false,
  r_good_behaviour BOOLEAN NOT NULL DEFAULT false,
  p_overdue BOOLEAN NOT NULL DEFAULT false,
  p_rework INTEGER NOT NULL DEFAULT 0,
  p_failure BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT now(),
  task_id UUID NOT NULL,
  employee_id UUID NULL,
  CONSTRAINT rl_miles_pkey PRIMARY KEY (id),
  CONSTRAINT fk_rl_miles_employee FOREIGN KEY (employee_id) REFERENCES user_miles (id) ON DELETE CASCADE,
  CONSTRAINT fk_rl_miles_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
) TABLESPACE pg_default;

-- Create unique constraint on task_id to prevent duplicate feedback
CREATE UNIQUE INDEX IF NOT EXISTS idx_rl_miles_task_id ON public.rl_miles(task_id);

-- Add RLS
ALTER TABLE public.rl_miles ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Managers can view RL feedback" ON public.rl_miles
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM public.user_miles
    WHERE auth_id = auth.uid()
      AND role IN ('manager', 'admin')
  )
);

CREATE POLICY "System can insert RL feedback" ON public.rl_miles
FOR INSERT WITH CHECK (true);

CREATE POLICY "System can update RL feedback" ON public.rl_miles
FOR UPDATE USING (true);

-- Add comments for documentation
COMMENT ON TABLE public.rl_miles IS 'Reinforcement Learning feedback data for task assignments - automatically calculated';
COMMENT ON COLUMN public.rl_miles.r_completion IS 'Reward: Task was completed successfully';
COMMENT ON COLUMN public.rl_miles.r_ontime IS 'Reward: Task was completed on time (not overdue)';
COMMENT ON COLUMN public.rl_miles.r_good_behaviour IS 'Reward: Task completed within expected time for difficulty';
COMMENT ON COLUMN public.rl_miles.p_overdue IS 'Penalty: Task was overdue when completed';
COMMENT ON COLUMN public.rl_miles.p_rework IS 'Penalty: Task required rework (future use)';
COMMENT ON COLUMN public.rl_miles.p_failure IS 'Penalty: Task was failed/not completed (future use)';