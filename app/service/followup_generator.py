"""Follow-up question generator for vague intent - Layer 2a."""

from app.prompts.followup import FOLLOWUP_GENERATOR
from app.service.llm_client import complete


def generate_followup_question(user_message: str, followup_reason: str) -> str:
    """Generate a clarifying question when user intent is vague."""
    reason = followup_reason or "occasion and budget unclear"
    user_content = f"User said: \"{user_message}\"\n\nWe need to ask about: {reason}"
    return complete(FOLLOWUP_GENERATOR, user_content).strip()
