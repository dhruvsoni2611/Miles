"""
Assignment Engine - Miles Brain v1
Uses weighted scoring:
40% Skill Fit  (vector + explicit)
20% History Bonus (past success via assignments)
15% Performance / Momentum
25% Burnout Penalty

This engine reads from our schema tables:
users, user_skills, task_skill_requirements, assignments
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import numpy as np
from core.database import get_supabase_client

logger = logging.getLogger(__name__)

class AssignmentEngine:
    def __init__(self):
        self.supabase = get_supabase_client()

    # ----------------- FETCHING DATA FROM SCHEMA ------------------ #

    def fetch_candidates(self) -> List[Dict[str, Any]]:
        """Get all employees (role = 'employee')"""
        try:
            res = self.supabase.table("user_miles")\
                .select("*")\
                .eq("role", "employee")\
                .limit(100)\
                .execute()
                
            return res.data or []
        except Exception as e:
            logger.error(f"fetch_candidates failed: {e}")
            return []


    def fetch_user_skills(self, user_id: UUID) -> Dict[str, float]:
        """Fetch mapped user skills -> proficiency"""
        try:
            res = self.supabase.table("user_skills")\
                .select("skill_id, proficiency, skills(name)")\
                .eq("user_id", str(user_id))\
                .execute()

            skills = {}
            for row in res.data or []:
                skill_name = row.get("skills", {}).get("name", "").lower()
                skills[skill_name] = row.get("proficiency", 1) / 10  # convert 1-10 -> 0-1 weight

            return skills
        except Exception as e:
            logger.error(f"fetch_user_skills failed: {e}")
            return {}


    def fetch_task_required_skills(self, task_id: UUID) -> List[Dict[str, Any]]:
        """Fetch required skills for a given task"""
        try:
            res = self.supabase.table("task_skill_requirements")\
                .select("skill_id, required_level, skills(name)")\
                .eq("task_id", str(task_id))\
                .execute()

            requirements = []
            for row in res.data or []:
                requirements.append({
                    "skill": row.get("skills", {}).get("name", "").lower(),
                    "required_level": row.get("required_level", 1) / 10  # normalize
                })

            return requirements
        except Exception as e:
            logger.error(f"fetch_task_required_skills failed: {e}")
            return []


    def fetch_user_performance_history(self, user_id: UUID) -> float:
        """Look at past assignments to compute quality momentum."""
        try:
            res = self.supabase.table("assignments")\
                .select("outcome_score")\
                .eq("user_id", str(user_id))\
                .order("assigned_at", desc=True)\
                .limit(10).execute()

            # Filter out assignments that haven't been completed/scored yet
            scores = [r.get("outcome_score", 0.5) for r in res.data or [] if r.get("outcome_score") is not None]
            
            # Default to neutral 0.5 if no history
            return sum(scores) / len(scores) if scores else 0.5
        except Exception as e:
            logger.error(f"fetch_user_performance_history failed: {e}")
            return 0.5


    # ----------------- SCORE CALCULATIONS ------------------ #

    def _vector_similarity(self, u_vec: Any, t_vec: Any) -> float:
        """Cosine similarity on stored vectors (later embeddings)."""
        if not u_vec or not t_vec:
            return 0.0
        
        try:
            v1 = np.array(u_vec, dtype=float)
            v2 = np.array(t_vec, dtype=float)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
                
            return float(np.dot(v1, v2) / (norm_v1 * norm_v2))
        except:
            return 0.0


    def _skill_match_score(self, user_skills: Dict[str, float], req_skills: List[Dict[str, Any]]) -> float:
        """Match required vs user skills"""
        if not req_skills: return 1.0
        
        total, matched = 0, 0
        for req in req_skills:
            skl = req["skill"]
            needed = req["required_level"]
            if skl in user_skills:
                # Skill match is valid if user has the skill. 
                # We can refine this: maybe penalty if proficiency < needed? 
                # For now, simple weight logic.
                matched += min(user_skills[skl], needed)  # skill_weight in [0,1]
            total += 1
        return matched / total if total > 0 else 0.0


    async def calculate_score(self, user, task_id, task_req_skills) -> Dict[str, Any]:
        """Calculates the weighted score for a user against a task without side effects."""
        
        # ----- Skill Score 40% -----
        user_skills = self.fetch_user_skills(user["id"])
        skill_score = self._skill_match_score(user_skills, task_req_skills)

        # ----- History Bonus 20% -----
        # History is usually 0.0 to 1.0 based on outcome_score
        raw_history = self.fetch_user_performance_history(user["id"])
        
        # ----- Performance Momentum 15% -----
        # productivity_score in DB
        perf_score = user.get("productivity_score", 0.0) 
        if perf_score is None: perf_score = 0.0

        # ----- Burnout / Workload Advisory (not blocking) -----
        load = user.get("workload", 0.0) or 0.0
        burnout = 0.0  # placeholder
        health_cost = ((load * 0.5) + (burnout * 0.8)) * 0.25

        final = (0.40 * skill_score) + (0.20 * raw_history) + (0.15 * perf_score) - health_cost
        total_score = max(final, 0.01)

        workload_indicator = "low"
        if load >= 0.66:
            workload_indicator = "high"
        elif load >= 0.33:
            workload_indicator = "medium"

        return {
            "user_id": user["id"],
            "total_score": total_score,
            "reasons": {
                "skill_match_score": skill_score,
                "productivity_score": perf_score,
                "workload_indicator": workload_indicator,
            }
        }


    # ----------------- SUGGESTION ENTRYPOINT (READ-ONLY) ------------------ #

    async def suggest_for_task(self, task_id: UUID) -> Dict[str, Any]:
        """
        Compute ranked candidate suggestions for a task.
        No side effects. Returns sorted list with reason breakdown.
        """
        try:
            task_req = self.fetch_task_required_skills(task_id)
            users = self.fetch_candidates()

            if not users:
                logger.warning("No candidates found.")
                return {"task_id": str(task_id), "suggestions": []}

            scored_candidates = []
            for u in users:
                score_data = await self.calculate_score(u, task_id, task_req)
                scored_candidates.append(score_data)

            scored_candidates.sort(key=lambda x: x["total_score"], reverse=True)

            return {
                "task_id": str(task_id),
                "suggestions": scored_candidates
            }

        except Exception as e:
            logger.error(f"AssignmentEngine Failure: {e}")
            return {"task_id": str(task_id), "suggestions": [], "error": str(e)}
