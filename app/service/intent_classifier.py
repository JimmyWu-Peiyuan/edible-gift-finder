"""Intent classification for customer queries - Layer 1 of AI product discovery."""

from typing import TypedDict

from app.prompts.intent import INTENT_CLASSIFIER
from app.service.llm_client import complete_json


class Intent(TypedDict):
    """Structured intent from user message."""

    intent_type: str
    keywords: list[str]
    needs_followup: bool
    followup_reason: str | None
    comparison_requested: bool
    products_to_compare: list[str]
    confidence: str


def get_intent(
    user_message: str,
    conversation_history: list[dict] | None = None,
    *,
    recent_recommendations_shown: bool = False,
    recent_product_names: list[str] | None = None,
) -> Intent:
    """
    Classify user intent from their message.

    Args:
        user_message: The user's current message.
        conversation_history: Optional list of {"role": "user"|"assistant", "content": "..."} for context.
        recent_recommendations_shown: If True, the assistant just showed product recommendations;
            the user's message may be feedback (e.g. "cheaper", "more fun").

    Returns:
        Intent dict with intent_type, keywords, needs_followup, etc.
    """
    if conversation_history:
        context = "\n".join(
            f"{m['role']}: {m['content']}" for m in conversation_history[-6:]
        )
        user_content = f"Previous conversation:\n{context}\n\nLatest user message: {user_message}"
    else:
        user_content = user_message

    if recent_recommendations_shown:
        user_content += "\n\n[Context: The assistant just showed product recommendations. The user may be giving feedback on those (e.g. cheaper, more fun, something different).]"

    if recent_product_names:
        user_content += f"\n\n[Recently shown products (use these names for 'compare these' or 'first two'): {', '.join(recent_product_names)}]"

    result = complete_json(INTENT_CLASSIFIER, user_content)

    products_to_compare = result.get("products_to_compare")
    if not isinstance(products_to_compare, list):
        products_to_compare = []

    return Intent(
        intent_type=result.get("intent_type", "vague"),
        keywords=result.get("keywords") or [],
        needs_followup=bool(result.get("needs_followup", False)),
        followup_reason=result.get("followup_reason"),
        comparison_requested=bool(result.get("comparison_requested", False)),
        products_to_compare=products_to_compare,
        confidence=result.get("confidence", "medium"),
    )
