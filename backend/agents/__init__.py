# Agents package for Miles platform
# This package will contain various AI/ML agents

# Conditional imports - ML agents require sklearn
try:
    from .reward_calculation import get_reward_calculator, calculate_task_reward
    from .contextual_bandit import get_contextual_bandit_agent
    from .skill_similarity_filter import get_skill_similarity_filter, filter_employees_by_skill_similarity
    __all__ = [
        'get_reward_calculator',
        'calculate_task_reward',
        'get_contextual_bandit_agent',
        'get_skill_similarity_filter',
        'filter_employees_by_skill_similarity'
    ]
except ImportError as e:
    # If ML dependencies are not available, provide None or stub functions
    import warnings
    warnings.warn(f"ML agents not available: {e}. Install scikit-learn and pandas to enable ML features.")
    
    def get_reward_calculator():
        raise ImportError("scikit-learn is required for reward calculation. Install with: pip install scikit-learn")
    
    def calculate_task_reward(*args, **kwargs):
        raise ImportError("scikit-learn is required for reward calculation. Install with: pip install scikit-learn")
    
    def get_contextual_bandit_agent():
        raise ImportError("scikit-learn is required for contextual bandit. Install with: pip install scikit-learn")
    
    def get_skill_similarity_filter():
        raise ImportError("scikit-learn is required for skill similarity. Install with: pip install scikit-learn")
    
    def filter_employees_by_skill_similarity(*args, **kwargs):
        raise ImportError("scikit-learn is required for skill similarity. Install with: pip install scikit-learn")
    
    __all__ = [
        'get_reward_calculator',
        'calculate_task_reward',
        'get_contextual_bandit_agent',
        'get_skill_similarity_filter',
        'filter_employees_by_skill_similarity'
    ]