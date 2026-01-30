"""
OpenAI embeddings for employee skills.
Generates embeddings for skill names and stores them in user_miles.skill_vector.
"""

import os
from typing import List, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_skill_embeddings(skills: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """
    Create embeddings for a list of skills using OpenAI API.

    Args:
        skills: List of skill name strings
        model: OpenAI embedding model (default: text-embedding-3-small)

    Returns:
        List of embedding vectors, one per skill. Empty list if no skills or API fails.
    """
    if not skills:
        return []

    # Filter out empty strings
    skill_list = [s.strip() for s in skills if s and s.strip()]

    if not skill_list:
        return []

    if not OPENAI_AVAILABLE:
        logger.warning("OpenAI package not available, cannot generate embeddings")
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, cannot generate embeddings")
        return []

    try:
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=model,
            input=skill_list
        )

        # response.data is in same order as input
        embeddings_list = [item.embedding for item in response.data]

        logger.info(f"Generated {len(embeddings_list)} OpenAI embeddings for skills")
        return embeddings_list

    except Exception as e:
        logger.error(f"Failed to generate OpenAI embeddings: {e}")
        return []
