"""Modular prompts for AI product discovery."""

from app.prompts.components import GROUNDING_RULES, ROLE, TONE
from app.prompts.followup import FOLLOWUP_GENERATOR
from app.prompts.intent import INTENT_CLASSIFIER
from app.prompts.recommender import (
    RECOMMENDER_SYSTEM,
    RECOMMENDER_USER_TEMPLATE,
    FALLBACK_NO_KEYWORDS,
    FALLBACK_NO_PRODUCTS,
)

__all__ = [
    "ROLE",
    "TONE",
    "GROUNDING_RULES",
    "INTENT_CLASSIFIER",
    "FOLLOWUP_GENERATOR",
    "RECOMMENDER_SYSTEM",
    "RECOMMENDER_USER_TEMPLATE",
    "FALLBACK_NO_KEYWORDS",
    "FALLBACK_NO_PRODUCTS",
]
