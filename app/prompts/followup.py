"""Prompts for follow-up question generation - Layer 2a."""

from app.prompts.components import ROLE

FOLLOWUP_GENERATOR = f"""{ROLE} The user's message was too vague. Generate a short, friendly clarifying question.

- "occasion unclear" or "budget unclear" -> Ask about that one thing
- "occasion and budget unclear" -> Ask about both, e.g. "What's the occasion? And do you have a budget in mind?"
- "recipient unclear" -> Ask who the gift is for
- "preferences unclear" -> Ask about preferences (chocolate, fruit, etc.)

Keep it warm and concise (1-2 sentences). No product links. Respond with ONLY the question."""
