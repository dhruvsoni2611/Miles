# Skill Similarity Filter Implementation

## Overview

The skill similarity filter is a two-stage filtering system that optimizes task assignment:

1. **Stage 1: Skill Similarity Filter** - Filters employees to top 3 based on cosine similarity between task and employee skill embeddings
2. **Stage 2: RL Agent Selection** - Contextual bandit selects the best employee from the top 3 skill-matched candidates

## How It Works

### Stage 1: Skill Similarity Filtering

1. **Extract Task Skill Embeddings**
   - Reads `skill_embedding` field from task (JSONB array of embeddings)
   - If missing, generates embeddings using OpenAI API from `required_skills` names

2. **Extract Employee Skill Embeddings**
   - Reads `skill_vector` field from employee (JSONB array of embeddings)
   - If missing, generates embeddings using OpenAI API from skill names

3. **Calculate Cosine Similarity**
   - Compares each task skill embedding with each employee skill embedding
   - Calculates average cosine similarity across all pairs
   - Returns similarity score (0.0 to 1.0)

4. **Filter to Top 3**
   - Sorts employees by similarity score (highest first)
   - Returns top 3 employees

### Stage 2: RL Agent Selection

- Only the top 3 employees from Stage 1 are passed to the contextual bandit
- RL agent uses 8-dimensional feature space to select final employee
- Considers: productivity, workload, task priority/difficulty, skill match, urgency, etc.

## API Integration

### Task Assignment Endpoint

```
PUT /tasks/{task_id}/assign?use_bandit=true
```

**Flow:**
1. Get all assignable employees
2. **Filter to top 3 by skill similarity** ← NEW
3. Pass top 3 to RL agent
4. RL agent selects final employee
5. Assign task to selected employee

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### OpenAI Model

Default: `text-embedding-3-small`

Can be configured in `SkillSimilarityFilter.__init__()`:
```python
filter_instance = SkillSimilarityFilter(openai_model="text-embedding-3-large")
```

## Data Structure

### Task Data
```json
{
  "skill_embedding": [
    [0.123, -0.456, ...],  // Embedding for skill 1
    [0.789, 0.234, ...]    // Embedding for skill 2
  ],
  "required_skills": ["Python", "SQL"]  // Fallback if embeddings missing
}
```

### Employee Data
```json
{
  "skill_vector": [
    [0.345, -0.678, ...],  // Embedding for skill 1
    [0.901, 0.123, ...]    // Embedding for skill 2
  ],
  "skills": ["Python", "JavaScript"]  // Fallback if embeddings missing
}
```

## Example Usage

```python
from agents.skill_similarity_filter import filter_employees_by_skill_similarity

# Task data with skill embeddings
task_data = {
    "skill_embedding": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
    "required_skills": ["Python", "SQL"]
}

# List of employees
employees = [
    {"auth_id": "emp1", "skill_vector": [[0.1, 0.2, ...]]},
    {"auth_id": "emp2", "skill_vector": [[0.3, 0.4, ...]]},
    {"auth_id": "emp3", "skill_vector": [[0.5, 0.6, ...]]},
    # ... more employees
]

# Filter to top 3
top_3_employees = filter_employees_by_skill_similarity(
    task_data,
    employees,
    top_k=3
)
```

## Benefits

1. **Efficiency**: Reduces RL agent computation by filtering to relevant candidates first
2. **Accuracy**: Ensures only skill-matched employees are considered
3. **Performance**: Faster task assignment with fewer candidates to evaluate
4. **Quality**: Combines semantic skill matching (OpenAI embeddings) with contextual optimization (RL agent)

## Fallback Behavior

- If OpenAI API is unavailable: Uses existing embeddings from database
- If no embeddings exist: Returns all employees (no filtering)
- If filtering fails: Falls back to all employees, RL agent still works

## Logging

The filter logs:
- Number of employees filtered
- Similarity scores for top employees
- OpenAI embedding generation status
- Any errors or fallbacks
