"""
Contextual Bandit Agent for Task Assignment Optimization
Implements contextual bandit algorithm for optimal employee-task assignments
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timezone
import logging
import pickle
import os
import json

logger = logging.getLogger(__name__)

class ContextualBanditAgent:
    """
    Contextual Bandit Agent for task assignment optimization.

    Uses logistic regression models (one per employee) to predict expected rewards
    based on task-employee context features.
    """

    def __init__(
        self,
        n_features: int = 8,
        exploration_rate: float = 0.1,
        model_path: str = "models/bandit_models.pkl"
    ):
        """
        Initialize the contextual bandit agent.

        Args:
            n_features: Number of context features
            exploration_rate: Probability of random action (ε-greedy)
            model_path: Path to save/load trained models
        """
        self.n_features = n_features
        self.exploration_rate = exploration_rate
        self.model_path = model_path
        self.models = {}  # employee_id -> LogisticRegression model
        self.scalers = {}  # employee_id -> StandardScaler
        self.action_history = []  # For batch learning
        self.feature_names = [
            'employee_productivity',
            'employee_workload',
            'task_priority',
            'task_difficulty',
            'skill_match_score',
            'urgency_days',
            'task_complexity',
            'employee_experience_match'
        ]

        # Ensure model directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Load existing models if available
        self._load_models()

    def get_context_features(
        self,
        task_data: Dict,
        employee_data: Dict
    ) -> np.ndarray:
        """
        Extract context features for the task-employee pair.

        Args:
            task_data: Task information
            employee_data: Employee information

        Returns:
            Feature vector as numpy array
        """
        features = []

        # Employee features
        productivity = employee_data.get('productivity_score', 0.0)
        features.append(float(productivity))  # employee_productivity

        workload = employee_data.get('workload', 0) / 100.0  # Normalize to 0-1
        features.append(float(workload))  # employee_workload

        # Task features
        priority = task_data.get('priority_score', 2) / 4.0  # Normalize to 0-1
        features.append(float(priority))  # task_priority

        difficulty = task_data.get('difficulty_score', 1) / 10.0  # Normalize to 0-1
        features.append(float(difficulty))  # task_difficulty

        # Skill match score (simplified cosine similarity)
        skill_match = self._calculate_skill_match(task_data, employee_data)
        features.append(float(skill_match))  # skill_match_score

        # Urgency (days until due date)
        urgency = self._calculate_urgency(task_data)
        features.append(float(urgency))  # urgency_days

        # Task complexity (interaction between difficulty and priority)
        complexity = difficulty * priority
        features.append(float(complexity))  # task_complexity

        # Employee experience match
        experience_match = self._calculate_experience_match(task_data, employee_data)
        features.append(float(experience_match))  # employee_experience_match

        feature_vector = np.array(features, dtype=np.float32)

        # Validate feature vector
        if len(feature_vector) != self.n_features:
            logger.warning(f"Feature vector length mismatch: expected {self.n_features}, got {len(feature_vector)}")
            # Pad or truncate if necessary
            if len(feature_vector) < self.n_features:
                feature_vector = np.pad(feature_vector, (0, self.n_features - len(feature_vector)))
            else:
                feature_vector = feature_vector[:self.n_features]

        return feature_vector.reshape(1, -1)

    def _calculate_skill_match(self, task_data: Dict, employee_data: Dict) -> float:
        """Calculate skill match score between task requirements and employee skills."""
        try:
            task_skills = set(task_data.get('required_skills', []))
            employee_skills = set(employee_data.get('skills', []))

            if not task_skills:
                return 0.5  # Neutral score if no skills specified

            if not employee_skills:
                return 0.0  # No match if employee has no skills

            # Jaccard similarity
            intersection = len(task_skills.intersection(employee_skills))
            union = len(task_skills.union(employee_skills))

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            logger.warning(f"Error calculating skill match: {e}")
            return 0.5

    def _calculate_urgency(self, task_data: Dict) -> float:
        """Calculate task urgency in days until due date."""
        try:
            due_date_str = task_data.get('due_date')
            if not due_date_str:
                return 30.0  # Default 30 days if no due date

            # Parse due date
            if isinstance(due_date_str, str):
                if due_date_str.endswith('Z'):
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                else:
                    due_date = datetime.fromisoformat(due_date_str)
            else:
                due_date = due_date_str

            now = datetime.now(timezone.utc)
            days_until_due = (due_date - now).days

            # Transform to a 0-1 scale (more urgent = higher value)
            urgency = 1.0 / (1.0 + max(0, days_until_due))  # Sigmoid-like transformation

            return min(urgency, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating urgency: {e}")
            return 0.5

    def _calculate_experience_match(self, task_data: Dict, employee_data: Dict) -> float:
        """Calculate experience match based on task difficulty and employee experience."""
        try:
            task_difficulty = task_data.get('difficulty_score', 1)
            employee_experience = employee_data.get('experience_years', {})

            if not employee_experience:
                return 0.0

            # Simple heuristic: higher experience = better for harder tasks
            total_experience_months = sum(employee_experience.values())
            experience_score = min(total_experience_months / 120, 1.0)  # Cap at 10 years

            # Match score: experience should be proportional to difficulty
            match_score = experience_score * (task_difficulty / 10.0)

            return min(match_score, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating experience match: {e}")
            return 0.5

    def select_action(
        self,
        context: np.ndarray,
        available_employees: List[str],
        task_data: Optional[Dict] = None
    ) -> str:
        """
        Select the best employee using contextual bandit algorithm.

        Args:
            context: Context features for the task
            available_employees: List of available employee IDs
            task_data: Optional task data for logging

        Returns:
            Selected employee ID
        """
        if not available_employees:
            raise ValueError("No employees available for assignment")

        # ε-greedy exploration
        if np.random.random() < self.exploration_rate:
            selected_employee = np.random.choice(available_employees)
            logger.info(f"Bandit exploration: randomly selected employee {selected_employee}")
            return selected_employee

        # Exploitation: select employee with highest predicted reward
        best_employee = None
        best_score = -float('inf')

        for employee_id in available_employees:
            if employee_id not in self.models:
                # Cold start: use heuristic score
                score = self._cold_start_score(employee_id)
            else:
                # Predict expected reward using trained model
                model = self.models[employee_id]
                scaler = self.scalers.get(employee_id)

                # Scale features if scaler exists
                scaled_context = context
                if scaler:
                    try:
                        scaled_context = scaler.transform(context)
                    except:
                        pass  # Use unscaled if scaling fails

                # Predict probability of positive reward
                try:
                    score = model.predict_proba(scaled_context)[0][1]
                except Exception as e:
                    logger.warning(f"Error predicting with model for {employee_id}: {e}")
                    score = self._cold_start_score(employee_id)

            if score > best_score:
                best_score = score
                best_employee = employee_id

        logger.info(
            f"Bandit exploitation: selected employee {best_employee} "
            f"with predicted score {best_score:.3f}"
        )

        return best_employee

    def _cold_start_score(self, employee_id: str) -> float:
        """Provide initial score for new employees (cold start problem)."""
        # Use a random score with slight positive bias
        return 0.5 + np.random.normal(0, 0.1)

    def update_model(
        self,
        employee_id: str,
        context: np.ndarray,
        reward: float,
        batch_update: bool = True
    ):
        """
        Update the model for an employee based on observed reward.

        Args:
            employee_id: Employee ID
            context: Context features
            reward: Observed reward
            batch_update: Whether to batch updates or update immediately
        """
        # Convert reward to binary label for logistic regression
        label = 1 if reward > 0 else 0

        # Store for batch learning
        self.action_history.append({
            'employee_id': employee_id,
            'context': context.flatten(),
            'reward': reward,
            'label': label,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        if batch_update:
            # Batch update every 10 samples per employee
            employee_samples = [h for h in self.action_history if h['employee_id'] == employee_id]
            if len(employee_samples) >= 10:
                self._batch_update_employee_model(employee_id)
        else:
            # Immediate update (less stable but more responsive)
            self._update_employee_model(employee_id, context, label)

    def _update_employee_model(self, employee_id: str, context: np.ndarray, label: int):
        """Update model for a single employee with one sample."""
        if employee_id not in self.models:
            self.models[employee_id] = LogisticRegression(
                random_state=42,
                max_iter=1000,
                class_weight='balanced'
            )
            self.scalers[employee_id] = StandardScaler()

        model = self.models[employee_id]
        scaler = self.scalers[employee_id]

        try:
            # Scale features
            scaled_context = scaler.fit_transform(context)

            # Fit model
            model.fit(scaled_context, [label])

            logger.info(f"Updated model for employee {employee_id} with single sample")

        except Exception as e:
            logger.error(f"Error updating model for employee {employee_id}: {e}")

    def _batch_update_employee_model(self, employee_id: str):
        """Batch update model for an employee using recent samples."""
        employee_samples = [h for h in self.action_history if h['employee_id'] == employee_id]

        if len(employee_samples) < 5:  # Minimum samples for training
            return

        # Prepare training data
        contexts = np.array([s['context'] for s in employee_samples])
        labels = np.array([s['label'] for s in employee_samples])

        if employee_id not in self.models:
            self.models[employee_id] = LogisticRegression(
                random_state=42,
                max_iter=1000,
                class_weight='balanced'
            )
            self.scalers[employee_id] = StandardScaler()

        model = self.models[employee_id]
        scaler = self.scalers[employee_id]

        try:
            # Scale features
            scaled_contexts = scaler.fit_transform(contexts)

            # Fit model
            model.fit(scaled_contexts, labels)

            # Remove processed samples from history
            self.action_history = [h for h in self.action_history if h['employee_id'] != employee_id]

            logger.info(f"Batch updated model for employee {employee_id} with {len(employee_samples)} samples")

        except Exception as e:
            logger.error(f"Error batch updating model for employee {employee_id}: {e}")

    def batch_update_all_models(self):
        """Batch update models for all employees with sufficient data."""
        employee_ids = set(h['employee_id'] for h in self.action_history)

        for employee_id in employee_ids:
            employee_samples = [h for h in self.action_history if h['employee_id'] == employee_id]
            if len(employee_samples) >= 5:
                self._batch_update_employee_model(employee_id)

    def save_models(self):
        """Save trained models to disk."""
        try:
            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'n_features': self.n_features,
                'exploration_rate': self.exploration_rate,
                'feature_names': self.feature_names
            }

            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"Saved bandit models to {self.model_path}")

        except Exception as e:
            logger.error(f"Error saving models: {e}")

    def _load_models(self):
        """Load trained models from disk."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)

                self.models = model_data.get('models', {})
                self.scalers = model_data.get('scalers', {})
                self.n_features = model_data.get('n_features', self.n_features)
                self.exploration_rate = model_data.get('exploration_rate', self.exploration_rate)
                self.feature_names = model_data.get('feature_names', self.feature_names)

                logger.info(f"Loaded bandit models from {self.model_path}")

        except Exception as e:
            logger.warning(f"Error loading models: {e}")
            # Initialize empty models
            self.models = {}
            self.scalers = {}

    def get_model_stats(self) -> Dict:
        """Get statistics about the trained models."""
        stats = {
            'total_models': len(self.models),
            'trained_employees': list(self.models.keys()),
            'total_samples': len(self.action_history),
            'samples_per_employee': {}
        }

        for employee_id in self.models.keys():
            samples = len([h for h in self.action_history if h['employee_id'] == employee_id])
            stats['samples_per_employee'][employee_id] = samples

        return stats

    def reset_models(self):
        """Reset all models (useful for testing or retraining)."""
        self.models = {}
        self.scalers = {}
        self.action_history = []

        if os.path.exists(self.model_path):
            os.remove(self.model_path)

        logger.info("Reset all bandit models")


# Global bandit agent instance
_bandit_agent = None

def get_contextual_bandit_agent() -> ContextualBanditAgent:
    """Get the global contextual bandit agent instance."""
    global _bandit_agent
    if _bandit_agent is None:
        _bandit_agent = ContextualBanditAgent()
    return _bandit_agent