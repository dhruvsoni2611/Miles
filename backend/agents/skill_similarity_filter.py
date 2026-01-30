"""
Skill Similarity Filter Module
Filters employees based on cosine similarity between task skill embeddings and employee skill embeddings.
Uses pre-computed embeddings from the database (no embedding generation here).
"""

import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class SkillSimilarityFilter:
    """
    Filters employees based on skill similarity using pre-computed embeddings.
    Calculates cosine similarity between task skill embeddings and employee skill embeddings.
    """

    def calculate_cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (float between -1 and 1)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Ensure same dimension
            if len(vec1) != len(vec2):
                logger.warning(f"Embedding dimension mismatch: {len(vec1)} vs {len(vec2)}")
                return 0.0

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0

    def calculate_average_similarity(
        self,
        task_embeddings: List[List[float]],
        employee_embeddings: List[List[float]]
    ) -> float:
        """
        Calculate average cosine similarity between task and employee skill embeddings.

        Args:
            task_embeddings: List of task skill embeddings
            employee_embeddings: List of employee skill embeddings

        Returns:
            Average cosine similarity score
        """
        if not task_embeddings or not employee_embeddings:
            return 0.0

        similarities = []

        # Compare each task skill with each employee skill
        for task_emb in task_embeddings:
            for emp_emb in employee_embeddings:
                similarity = self.calculate_cosine_similarity(task_emb, emp_emb)
                similarities.append(similarity)

        # Return average similarity
        if similarities:
            return float(np.mean(similarities))
        return 0.0

    def get_task_skill_embeddings(self, task_data: Dict) -> List[List[float]]:
        """
        Get task skill embeddings from task data (database only, no generation).

        Args:
            task_data: Task data dictionary

        Returns:
            List of skill embeddings
        """
        skill_embeddings = task_data.get('skill_embedding', [])

        if skill_embeddings and isinstance(skill_embeddings, list) and len(skill_embeddings) > 0:
            if isinstance(skill_embeddings[0], list):
                return skill_embeddings
            elif isinstance(skill_embeddings[0], (int, float)):
                return [skill_embeddings]

        return []

    def get_employee_skill_embeddings(self, employee_data: Dict) -> List[List[float]]:
        """
        Get employee skill embeddings from employee data (database only, no generation).

        Args:
            employee_data: Employee data dictionary

        Returns:
            List of skill embeddings
        """
        skill_vector = employee_data.get('skill_vector', [])
        if isinstance(skill_vector, list) and len(skill_vector) > 0:
            if isinstance(skill_vector[0], list):
                return skill_vector
            elif isinstance(skill_vector[0], (int, float)):
                return [skill_vector]

        return []

    def get_all_employee_similarities(
        self,
        task_data: Dict,
        employees: List[Dict]
    ) -> List[Tuple[Dict, float]]:
        """
        Calculate cosine similarity for all employees (no top_k limit).
        Returns list of (employee_data, similarity_score) sorted by similarity (highest first).

        Args:
            task_data: Task data with skill embeddings
            employees: List of employee data dictionaries

        Returns:
            List of tuples (employee_data, similarity_score) sorted by similarity (highest first)
        """
        if not employees:
            return []

        # Get task skill embeddings
        task_embeddings = self.get_task_skill_embeddings(task_data)

        if not task_embeddings:
            logger.warning("No task skill embeddings available, returning all employees with 0 similarity")
            return [(emp, 0.0) for emp in employees]

        # Calculate similarity for each employee
        employee_similarities = []

        for employee in employees:
            # Get employee skill embeddings
            employee_embeddings = self.get_employee_skill_embeddings(employee)

            if not employee_embeddings:
                similarity = 0.0
            else:
                similarity = self.calculate_average_similarity(
                    task_embeddings,
                    employee_embeddings
                )

            employee_similarities.append((employee, similarity))

        # Sort by similarity (highest first)
        employee_similarities.sort(key=lambda x: x[1], reverse=True)

        return employee_similarities

    def filter_top_employees(
        self,
        task_data: Dict,
        employees: List[Dict],
        top_k: int = 3
    ) -> List[Tuple[Dict, float]]:
        """
        Filter employees to top K based on skill similarity.

        Args:
            task_data: Task data with skill embeddings
            employees: List of employee data dictionaries
            top_k: Number of top employees to return (default: 3)

        Returns:
            List of tuples (employee_data, similarity_score) sorted by similarity (highest first)
        """
        all_similarities = self.get_all_employee_similarities(task_data, employees)
        top_employees = all_similarities[:top_k]

        logger.info(
            f"Filtered {len(employees)} employees to top {len(top_employees)} "
            f"with similarity scores: {[f'{s:.3f}' for _, s in top_employees]}"
        )

        return top_employees


# Global filter instance
_skill_similarity_filter = None

def get_skill_similarity_filter() -> SkillSimilarityFilter:
    """Get the global skill similarity filter instance."""
    global _skill_similarity_filter
    if _skill_similarity_filter is None:
        _skill_similarity_filter = SkillSimilarityFilter()
    return _skill_similarity_filter

def filter_employees_by_skill_similarity(
    task_data: Dict,
    employees: List[Dict],
    top_k: int = 3
) -> List[Dict]:
    """
    Convenience function to filter employees by skill similarity.

    Args:
        task_data: Task data with skill embeddings
        employees: List of employee data dictionaries
        top_k: Number of top employees to return (default: 3)

    Returns:
        List of top K employee data dictionaries (without similarity scores)
    """
    filter_instance = get_skill_similarity_filter()
    top_employees = filter_instance.filter_top_employees(task_data, employees, top_k)
    return [emp for emp, _ in top_employees]
