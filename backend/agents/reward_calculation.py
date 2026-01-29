"""
Reward Calculation Module for Contextual Bandit
Calculates rewards based on task completion outcomes with clipping
"""

import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RewardCalculator:
    """Calculates rewards for task assignments using the specified formula."""

    def __init__(self):
        """Initialize reward calculator with default parameters."""
        # Reward formula parameters
        self.completion_reward = 1.0
        self.on_time_reward = 0.5
        self.rating_reward = 0.5
        self.hard_task_bonus = 0.4
        self.good_behavior_reward = 0.2

        # Penalty parameters
        self.failure_penalty = 1.2
        self.rework_penalty = 0.5
        self.overdue_penalty_per_day = 0.15

        # Reward clipping bounds
        self.min_reward = -2.0
        self.max_reward = 2.0

        # Hard task threshold
        self.hard_task_threshold = 8

    def calculate_reward(
        self,
        task_data: Dict,
        employee_data: Dict,
        completion_data: Dict
    ) -> float:
        """
        Calculate reward using the specified formula:
        +1.0 completion + 0.5 on_time + 0.5 rating + 0.4 hard_task + 0.2 good_behavior
        -1.2 failure - 0.5 rework - 0.15 per_overdue_day

        Args:
            task_data: Task information
            employee_data: Employee information
            completion_data: Completion outcome data

        Returns:
            Clipped reward value between -2.0 and +2.0
        """
        reward = 0.0

        # Positive rewards
        if completion_data.get('completed', False):
            reward += self.completion_reward  # Task completion

            if completion_data.get('on_time', False):
                reward += self.on_time_reward  # On time completion

            if completion_data.get('user_rating', 0) > 0:
                reward += self.rating_reward  # User rating provided

            # Hard task bonus (difficulty >= 8)
            task_difficulty = task_data.get('difficulty_level', 1)
            if task_difficulty >= self.hard_task_threshold:
                reward += self.hard_task_bonus

            if completion_data.get('good_behavior', False):
                reward += self.good_behavior_reward  # Good behavior

        # Negative rewards (penalties)
        if completion_data.get('failed', False):
            reward -= self.failure_penalty  # Failure penalty

        if completion_data.get('rework_required', False):
            reward -= self.rework_penalty  # Rework penalty

        # Overdue penalty
        overdue_days = completion_data.get('overdue_days', 0)
        if overdue_days > 0:
            reward -= self.overdue_penalty_per_day * overdue_days

        # Apply reward clipping
        clipped_reward = np.clip(reward, self.min_reward, self.max_reward)

        logger.info(
            f"Task reward calculation: raw={reward:.3f}, clipped={clipped_reward:.3f}, "
            f"completed={completion_data.get('completed', False)}, "
            f"on_time={completion_data.get('on_time', False)}, "
            f"failed={completion_data.get('failed', False)}, "
            f"overdue_days={overdue_days}"
        )

        return clipped_reward

    def get_reward_bounds(self) -> tuple:
        """Get the minimum and maximum reward bounds."""
        return (self.min_reward, self.max_reward)

    def analyze_reward_components(
        self,
        task_data: Dict,
        employee_data: Dict,
        completion_data: Dict
    ) -> Dict:
        """
        Break down reward into components for analysis.

        Returns:
            Dictionary with individual reward components
        """
        components = {
            'completion': 0.0,
            'on_time': 0.0,
            'rating': 0.0,
            'hard_task': 0.0,
            'good_behavior': 0.0,
            'failure': 0.0,
            'rework': 0.0,
            'overdue': 0.0,
            'total_raw': 0.0,
            'total_clipped': 0.0
        }

        # Positive components
        if completion_data.get('completed', False):
            components['completion'] = self.completion_reward

            if completion_data.get('on_time', False):
                components['on_time'] = self.on_time_reward

            if completion_data.get('user_rating', 0) > 0:
                components['rating'] = self.rating_reward

            task_difficulty = task_data.get('difficulty_level', 1)
            if task_difficulty >= self.hard_task_threshold:
                components['hard_task'] = self.hard_task_bonus

            if completion_data.get('good_behavior', False):
                components['good_behavior'] = self.good_behavior_reward

        # Negative components
        if completion_data.get('failed', False):
            components['failure'] = -self.failure_penalty

        if completion_data.get('rework_required', False):
            components['rework'] = -self.rework_penalty

        overdue_days = completion_data.get('overdue_days', 0)
        components['overdue'] = -self.overdue_penalty_per_day * overdue_days

        # Totals
        components['total_raw'] = sum([
            components['completion'],
            components['on_time'],
            components['rating'],
            components['hard_task'],
            components['good_behavior'],
            components['failure'],
            components['rework'],
            components['overdue']
        ])

        components['total_clipped'] = np.clip(components['total_raw'], self.min_reward, self.max_reward)

        return components


# Global calculator instance
_reward_calculator = None

def get_reward_calculator() -> RewardCalculator:
    """Get the global reward calculator instance."""
    global _reward_calculator
    if _reward_calculator is None:
        _reward_calculator = RewardCalculator()
    return _reward_calculator

def calculate_task_reward(
    task_data: Dict,
    employee_data: Dict,
    completion_data: Dict
) -> float:
    """
    Convenience function to calculate task reward.

    Args:
        task_data: Task information
        employee_data: Employee information
        completion_data: Completion outcome data

    Returns:
        Clipped reward value
    """
    calculator = get_reward_calculator()
    return calculator.calculate_reward(task_data, employee_data, completion_data)