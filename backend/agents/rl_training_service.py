"""
Miles RLTrainingService
Handles:
- Feedback Storage (assignment completion)
- Reward Calculation (R_total)
- Employee Performance/Burnout Updates
- Future Skill Reinforcement Learning
"""

import logging
import json
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import math
from core.database import get_supabase_client

logger = logging.getLogger(__name__)


class RLTrainingService:
    def __init__(self):
        self.supabase = get_supabase_client()

    # ============ MAIN ENTRYPOINT (called when task is completed) ============ #

    async def submit_feedback(
        self,
        assignment_id: UUID,
        actual_hours: float,
        predicted_hours: float,
        bugs: int = 0,
        review_comments: int = 0,
        satisfaction_score: float = 5.0,
        skill_improvement: float = 0.0,
        confidence: float = 0.5,                  # system’s assignment confidence
        completed_at: Optional[str] = None
    ):
        """
        Save outcome + compute reward + update user RL profile.
        This is triggered when a task is completed.
        """

        try:
            # fetch assignment record
            assignment_res = self.supabase.table("assignments").select("*").eq("id", str(assignment_id)).single().execute()
            assignment = assignment_res.data
            if not assignment:
                return {"status": "error", "msg": "Assignment not found"}

            user_id = assignment["user_id"]
            task_id = assignment["task_id"]
            started_at = assignment.get("assigned_at")
            if started_at:
                # Handle ISO format variations if needed
                try:
                    started_at_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                except:
                    started_at_dt = datetime.now()
            else:
                started_at_dt = datetime.now()

            # Calculate burnout increase proxy
            hours = actual_hours or 1
            burnout_increase = (max(0, hours - 8) * 0.05) if hours > 8 else 0

            # Calculate reward using multi-objective reward function
            reward_obj = self.compute_reward(
                predicted=predicted_hours,
                actual=actual_hours,
                bugs=bugs,
                review_comments=review_comments,
                skill_improvement=skill_improvement,
                burnout=burnout_increase,
                satisfaction=satisfaction_score,
                confidence=confidence,
                success=1 if actual_hours <= predicted_hours else 0
            )

            reward = reward_obj["total"]

            # store feedback in assignments table itself (no extra table needed)
            # Schema has 'notes' as TEXT, so we stringify the reward details
            self.supabase.table("assignments").update({
                "completed_at": completed_at or datetime.now().isoformat(),
                "outcome_score": float(reward),
                "notes": json.dumps(reward_obj), # Serialized as requested by schema TEXT type
            }).eq("id", str(assignment_id)).execute()

            # update user performance profile
            days_taken = max(1, (datetime.now() - started_at_dt).days)
            await self.update_user_profile(user_id, reward, hours, days_taken, burnout_increase, task_id)

            return {
                "status": "success",
                "reward": reward,
                "components": reward_obj
            }
        except Exception as e:
            logger.error(f"submit_feedback failed: {e}")
            return {"status": "error", "msg": str(e)}


    # ============ REWARD FUNCTION (core RL logic) ============ #

    def compute_reward(self, predicted, actual, bugs, review_comments, skill_improvement,
                       burnout, success, confidence, satisfaction):
        """
        Multi-factor reward calculation:
        R_total = sum weighted((speed), (quality), (learning), (health), (decision accuracy), (satisfaction))
        """

        actual_safe = max(0.1, actual)
        predicted_safe = max(0.1, predicted)

        r1_speed       = math.log(predicted_safe / actual_safe)         # +ve if faster
        r2_quality     = 1 - (bugs*0.3 + review_comments*0.05)
        r3_learning    = skill_improvement                             # if upgraded skills
        r4_health      = -burnout                                      # penalize burnout
        r5_accuracy    = 1 - ((confidence - success)**2)               # assignment correctness
        r6_satisfaction= min(max(satisfaction/10, 0), 1)

        # weights sum to 1.0
        total = (
            0.25*r1_speed +
            0.25*r2_quality +
            0.15*r3_learning +
            0.15*r4_health +
            0.10*r5_accuracy +
            0.10*r6_satisfaction
        )

        return {
            "total": total,
            "speed": r1_speed,
            "quality": r2_quality,
            "learning": r3_learning,
            "health_penalty": r4_health,
            "accuracy": r5_accuracy,
            "satisfaction": r6_satisfaction
        }


    # ============ POLICY UPDATE (where RL happens) ============ #

    async def update_user_profile(self, user_id, reward, hours, days, burnout_inc, task_id):
        """Update skill confidence, performance momentum, burnout adaptation."""

        try:
            # fetch user row
            user_res = self.supabase.table("user_miles").select("*").eq("id", str(user_id)).single().execute()
            user = user_res.data
            if not user: return

            # performance momentum update (productivity_score)
            old_perf = user.get("productivity_score", 0.5)
            if old_perf is None: old_perf = 0.5
            
            new_perf = old_perf + 0.1*(reward - old_perf)
            new_perf = min(max(new_perf, 0), 1)

            # NOTE: 'burnout_risk' is not in the current schema. 
            # We skip the specific column update to stay compatible.
            # Logic preserved below for reference if schema is updated later.
            # old_burn = user.get("burnout_risk", 0.0)
            # recovery = min(0.05, new_perf * 0.03)
            # new_burn = min(max(old_burn + burnout_inc - recovery, 0), 1)

            # Prepare update payload
            update_payload = {
                "productivity_score": float(new_perf),
                "updated_at": datetime.now().isoformat()
            }

            self.supabase.table("user_miles").update(update_payload).eq("id", str(user_id)).execute()

            logger.info(f"[RL] Updated user {user_id} → perf={new_perf}")
        except Exception as e:
            logger.error(f"update_user_profile failed: {e}")
