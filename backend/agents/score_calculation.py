"""
Productivity Score Calculation Module
Calculates employee productivity scores based on experience and tenure
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ProductivityCalculator:
    """Calculates productivity scores for employees based on experience and tenure."""

    def __init__(self):
        """Initialize the productivity calculator with default parameters."""
        # Configuration parameters
        self.max_experience_months = 120  # 10 years = fully experienced
        self.max_tenure_months = 60       # 5 years = fully adapted to company
        self.experience_weight = 0.4      # 40% weight for experience
        self.tenure_weight = 0.6          # 60% weight for company tenure

    def calculate_productivity_score(
        self,
        experience_months: int,
        tenure_months: int = 0
    ) -> float:
        """
        Calculate productivity score using weighted linear combination.

        Args:
            experience_months: Total months of professional experience
            tenure_months: Months worked at current company (default: 0 for new employees)

        Returns:
            Productivity score between 0.0 and 1.0
        """
        try:
            # Normalize experience score (cap at max_experience_months)
            exp_score = min(experience_months / self.max_experience_months, 1.0)

            # Normalize tenure score (cap at max_tenure_months)
            tenure_score = min(tenure_months / self.max_tenure_months, 1.0)

            # Weighted combination
            productivity = (exp_score * self.experience_weight) + (tenure_score * self.tenure_weight)

            # Ensure score is between 0 and 1
            productivity = max(0.0, min(1.0, productivity))

            logger.info(f"Calculated productivity score: {productivity:.3f} (exp: {experience_months} months, tenure: {tenure_months} months)")
            return round(productivity, 3)

        except Exception as e:
            logger.error(f"Error calculating productivity score: {e}")
            return 0.0

    def calculate_from_experience_and_tenure_data(
        self,
        experience_years: Dict[str, int],
        tenure_years: Optional[Dict[str, int]] = None
    ) -> float:
        """
        Calculate productivity score from experience_years and tenure_years data.

        Args:
            experience_years: Dictionary of skill -> months experience
            tenure_years: Dictionary of skill -> months tenure at company (optional)

        Returns:
            Productivity score between 0.0 and 1.0
        """
        try:
            if not experience_years:
                return 0.0

            # Calculate total experience across all skills
            total_experience_months = sum(experience_years.values())

            # Calculate total tenure - use provided tenure data or default to 0
            total_tenure_months = 0
            if tenure_years:
                total_tenure_months = sum(tenure_years.values())

            return self.calculate_productivity_score(total_experience_months, total_tenure_months)

        except Exception as e:
            logger.error(f"Error calculating productivity from experience and tenure data: {e}")
            return 0.0

    def calculate_from_experience_data(self, experience_years: Dict[str, int]) -> float:
        """
        Legacy method for backward compatibility.
        Calculate productivity score from experience_years data only.
        Uses experience as tenure proxy for new employees.

        Args:
            experience_years: Dictionary of skill -> months experience

        Returns:
            Productivity score between 0.0 and 1.0
        """
        return self.calculate_from_experience_and_tenure_data(experience_years, None)

    def update_score_with_tenure(
        self,
        current_score: float,
        total_experience_months: int,
        new_tenure_months: int
    ) -> float:
        """
        Update productivity score when tenure changes.

        Args:
            current_score: Current productivity score
            total_experience_months: Total professional experience
            new_tenure_months: Updated months at company

        Returns:
            Updated productivity score
        """
        return self.calculate_productivity_score(total_experience_months, new_tenure_months)


# Global calculator instance
_productivity_calculator = None

def get_productivity_calculator() -> ProductivityCalculator:
    """Get the global productivity calculator instance."""
    global _productivity_calculator
    if _productivity_calculator is None:
        _productivity_calculator = ProductivityCalculator()
    return _productivity_calculator

def calculate_employee_productivity_score(
    experience_years: Optional[Dict[str, int]] = None,
    tenure_years: Optional[Dict[str, int]] = None,
    experience_months: Optional[int] = None,
    tenure_months: int = 0
) -> float:
    """
    Convenience function to calculate productivity score for an employee.

    Args:
        experience_years: Skill-based experience data (for new employees)
        tenure_years: Skill-based tenure data (for new employees)
        experience_months: Total experience months (alternative input)
        tenure_months: Months at company (alternative input)

    Returns:
        Productivity score between 0.0 and 1.0
    """
    calculator = get_productivity_calculator()

    if experience_years is not None:
        return calculator.calculate_from_experience_and_tenure_data(experience_years, tenure_years)
    elif experience_months is not None:
        return calculator.calculate_productivity_score(experience_months, tenure_months)
    else:
        return 0.0