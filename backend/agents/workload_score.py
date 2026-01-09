"""
Workload Score Calculator Module
Calculates workload scores for employees based on their current task assignments
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class WorkloadScoreCalculator:
    """Calculates workload metrics for employees."""

    def __init__(self):
        """Initialize workload calculator with default parameters."""
        # Workload score parameters
        self.max_reasonable_tasks = 5  # Maximum tasks before overload
        self.task_weight_factor = 0.2  # How much each task affects workload

        # Priority score parameters (weighted by urgency)
        self.priority_weights = {
            1: 0.1,  # low
            2: 0.2,  # medium
            3: 0.4,  # high
            4: 0.8,  # urgent
            5: 1.0   # critical (if added)
        }

    def calculate_workload_score(self, current_tasks: List[Dict]) -> float:
        """
        Calculate workload score based on current task count and status.

        Args:
            current_tasks: List of current tasks assigned to employee

        Returns:
            Workload score (0.0 = no workload, 1.0 = fully loaded/overloaded)
        """
        if not current_tasks:
            return 0.0

        # Count active tasks (not done and not in review)
        active_tasks = [t for t in current_tasks if t.get('status') not in ['done', 'review']]

        # Base workload from task count
        task_count_score = min(len(active_tasks) / self.max_reasonable_tasks, 1.0)

        # Factor in task difficulty
        difficulty_factor = 0.0

        for task in active_tasks:
            # Difficulty contribution (1-10 scale, normalized)
            difficulty = task.get('difficulty_score', 1) / 10.0
            difficulty_factor += difficulty * 0.1  # Weight each task

        # Factor in task priority/urgency stress
        priority_stress_factor = self.calculate_workload_priority_score(active_tasks) * 0.15

        # Combine factors: volume + complexity + urgency
        workload_score = task_count_score + difficulty_factor + priority_stress_factor
        return min(workload_score, 1.0)

    def calculate_workload_priority_score(self, current_tasks: List[Dict]) -> float:
        """
        Calculate workload priority score based on priority of current tasks.

        Args:
            current_tasks: List of current tasks assigned to employee

        Returns:
            Priority score (0.0 = only low priority, 1.0 = only urgent tasks)
        """
        if not current_tasks:
            return 0.0

        active_tasks = [t for t in current_tasks if t.get('status') not in ['done', 'review']]
        if not active_tasks:
            return 0.0

        # Calculate weighted average priority
        total_weight = 0.0
        weighted_sum = 0.0

        for task in active_tasks:
            priority = task.get('priority_score', 2)  # Default to medium
            weight = self.priority_weights.get(priority, 0.2)

            weighted_sum += weight
            total_weight += 1.0

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_employee_workload_score(self, employee_id: str, supabase_client) -> int:
        """
        Calculate and return a single workload score for an employee as an integer.

        Args:
            employee_id: Employee UUID
            supabase_client: Supabase client instance

        Returns:
            Workload score as integer (0-100, where 100 = fully loaded)
        """
        try:
            # Get current tasks for employee
            current_tasks = supabase_client.table('tasks').select(
                'id, status, priority_score, difficulty_score'
            ).eq('assigned_to', employee_id).execute()

            tasks_data = current_tasks.data or []

            # Calculate workload score (0.0 to 1.0)
            workload_float = self.calculate_workload_score(tasks_data)

            # Convert to integer (0-100)
            workload_int = int(workload_float * 100)

            # Ensure it's within bounds
            workload_int = max(0, min(100, workload_int))

            return workload_int

        except Exception as e:
            logger.error(f"Error calculating workload score for employee {employee_id}: {e}")
            return 0

    def update_employee_workload_score(self, employee_id: str, supabase_client) -> bool:
        """
        Calculate and update the workload score for an employee in the database.

        Args:
            employee_id: Employee UUID
            supabase_client: Supabase client instance

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get current workload score
            workload_score = self.get_employee_workload_score(employee_id, supabase_client)

            # Update employee record with new workload score
            update_data = {
                'workload': workload_score,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            # Update the user_miles table
            response = supabase_client.table('user_miles').update(update_data).eq('auth_id', employee_id).execute()

            if response.data and len(response.data) > 0:
                logger.info(f"Updated workload score for employee {employee_id}: workload={workload_score}")
                return True
            else:
                logger.warning(f"No employee record found to update for {employee_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating workload score for employee {employee_id}: {e}")
            return False

# Global calculator instance
_workload_score_calculator = None

def get_workload_score_calculator() -> WorkloadScoreCalculator:
    """Get the global workload score calculator instance."""
    global _workload_score_calculator
    if _workload_score_calculator is None:
        _workload_score_calculator = WorkloadScoreCalculator()
    return _workload_score_calculator