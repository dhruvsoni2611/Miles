# Embeddings file for Miles platform
# This file will handle all embedding-related operations

import numpy as np
import os
import json
from typing import List, Union, Optional
import logging

# Try to import sentence_transformers, fallback to mock if not available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence_transformers not available, using mock embeddings")

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    """Manages embeddings for the Miles platform using sentence transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embeddings manager with a sentence transformer model.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence_transformers not available, using mock embeddings")
            self.model = None
            return

        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise

    def generate_skill_embeddings(self, skills: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of skills.

        Args:
            skills: List of skill names/strings

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        if not skills:
            return []

        if self.model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Embedding model not loaded")

        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None:
                # Generate mock embeddings (random vectors)
                import random
                embedding_dim = 384  # Standard dimension for sentence transformers
                embeddings_list = []
                for skill in skills:
                    # Create a deterministic mock embedding based on skill name
                    random.seed(hash(skill) % 10000)  # Deterministic seed
                    embedding = [random.uniform(-1, 1) for _ in range(embedding_dim)]
                    embeddings_list.append(embedding)
                logger.warning(f"Generated mock embeddings for {len(skills)} skills (sentence_transformers not available)")
                return embeddings_list

            # Generate real embeddings for each skill
            embeddings = self.model.encode(skills, convert_to_tensor=False)
            # Convert numpy arrays to lists for JSON serialization
            embeddings_list = [embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                             for embedding in embeddings]
            logger.info(f"Generated real embeddings for {len(skills)} skills")
            return embeddings_list
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def generate_combined_skill_embedding(self, skills: List[str]) -> Optional[List[float]]:
        """
        Generate a single combined embedding from multiple skills.
        Useful when you want one vector representation for all skills.

        Args:
            skills: List of skill names/strings

        Returns:
            Single embedding vector (list of floats) or None if no skills
        """
        if not skills:
            return None

        if self.model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Embedding model not loaded")

        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None:
                # Generate mock combined embedding
                import random
                embedding_dim = 384  # Standard dimension for sentence transformers
                combined_text = " ".join(skills)
                random.seed(hash(combined_text) % 10000)  # Deterministic seed
                embedding = [random.uniform(-1, 1) for _ in range(embedding_dim)]
                logger.warning(f"Generated mock combined embedding for {len(skills)} skills (sentence_transformers not available)")
                return embedding

            # Combine all skills into one text for a single embedding
            combined_text = " ".join(skills)
            embedding = self.model.encode([combined_text], convert_to_tensor=False)[0]
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            logger.info(f"Generated combined embedding for {len(skills)} skills")
            return embedding_list
        except Exception as e:
            logger.error(f"Failed to generate combined embedding: {e}")
            raise

    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (float between -1 and 1)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

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

# Global embeddings manager instance
_embeddings_manager = None

def get_embeddings_manager() -> EmbeddingsManager:
    """Get the global embeddings manager instance."""
    global _embeddings_manager
    if _embeddings_manager is None:
        _embeddings_manager = EmbeddingsManager()
    return _embeddings_manager

def create_skill_embeddings(skills: Union[str, List[str]]) -> Union[List[List[float]], List[float], None]:
    """
    Create embeddings for skills. This is the main entry point for the application.

    Args:
        skills: Either a comma-separated string of skills or a list of skill strings

    Returns:
        List of embeddings for individual skills, or None if no skills provided
    """
    if not skills:
        return None

    # Convert string to list if needed
    if isinstance(skills, str):
        # Split by comma and clean up whitespace
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
    else:
        skills_list = skills

    if not skills_list:
        return None

    manager = get_embeddings_manager()
    return manager.generate_skill_embeddings(skills_list)

def create_combined_skill_embedding(skills: Union[str, List[str]]) -> Optional[List[float]]:
    """
    Create a single combined embedding from multiple skills.

    Args:
        skills: Either a comma-separated string of skills or a list of skill strings

    Returns:
        Single embedding vector or None if no skills provided
    """
    if not skills:
        return None

    # Convert string to list if needed
    if isinstance(skills, str):
        # Split by comma and clean up whitespace
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
    else:
        skills_list = skills

    if not skills_list:
        return None

    manager = get_embeddings_manager()
    return manager.generate_combined_skill_embedding(skills_list)

def regenerate_employee_embeddings(skill_names: List[str]) -> List[List[float]]:
    """
    Regenerate embeddings for an existing employee.
    Useful for backfilling embeddings on employees created before embedding support.

    Args:
        skill_names: List of skill names

    Returns:
        Array of embeddings/vectors, ready for database storage
    """
    try:
        if not skill_names:
            return []

        # Generate new embeddings
        embeddings = create_skill_embeddings(skill_names)
        return embeddings if embeddings else []
    except Exception as e:
        logger.error(f"Failed to regenerate embeddings: {e}")
        return []