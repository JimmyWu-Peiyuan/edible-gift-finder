"""Orchestrator - ties intent (Layer 1) to response (Layer 2)."""

from typing import TypedDict

from app.service.comparison import ComparisonResult, get_comparison
from app.service.followup_generator import generate_followup_question
from app.service.intent_classifier import Intent, get_intent
from app.service.llm_client import complete
from app.service.recommender import (
    REFINEMENT_SEARCH_ADDITIONS,
    RecommendationResult,
    get_recommendations,
)

GREETING_PROMPT = """You are a friendly gift shopping assistant for edible.com (Edible Arrangements). The user just said hello or greeted you (e.g. "hi", "how are you", "hey").

Respond warmly and naturally, like a real person. Keep it short (1-2 sentences). Then gently invite them to tell you what gift they're looking for—occasion, who it's for, or budget. Don't be robotic or salesy. Sound like a helpful friend."""


class OrchestratorResponse(TypedDict):
    """Response from the orchestrator."""

    message: str
    products: list[dict]
    intent: Intent
    comparison_table: list[dict] | None


def respond(
    user_message: str,
    conversation_history: list[dict] | None = None,
    *,
    last_products: list[dict] | None = None,
    last_search_query: str | None = None,
    debug: bool = False,
) -> OrchestratorResponse:
    """
    Process user message and return appropriate response.

    Flow:
    - Classify intent (Layer 1)
    - If vague: generate clarifying question
    - If search/clarify: fetch products, generate recommendations
    - If refinement: re-search with feedback, exclude previous products
    - If compare: placeholder (suggest browsing for now)

    Args:
        user_message: The user's message.
        conversation_history: Optional list of {"role": "user"|"assistant", "content": "..."}.
        last_products: Products shown in the last assistant message (for refinement).
        last_search_query: The user message that led to last_products (for refinement).

    Returns:
        OrchestratorResponse with message, products, and intent.
    """
    recent_recs = bool(last_products and last_search_query)
    recent_product_names = (
        [p.get("name") for p in last_products if p.get("name")]
        if last_products
        else None
    )
    intent = get_intent(
        user_message,
        conversation_history,
        recent_recommendations_shown=recent_recs,
        recent_product_names=recent_product_names,
    )

    if intent["intent_type"] == "greeting":
        message = complete(GREETING_PROMPT, user_message).strip()
        return OrchestratorResponse(
            message=message,
            products=[],
            intent=intent,
            comparison_table=None,
        )

    if intent["needs_followup"] and not (intent["intent_type"] == "refinement" and recent_recs):
        message = generate_followup_question(
            user_message,
            intent.get("followup_reason") or "occasion and budget unclear",
        )
        return OrchestratorResponse(
            message=message,
            products=[],
            intent=intent,
            comparison_table=None,
        )

    if intent["comparison_requested"]:
        products_to_compare = intent.get("products_to_compare") or []
        if products_to_compare:
            result: ComparisonResult = get_comparison(
                products_to_compare,
                last_products=last_products,
            )
            return OrchestratorResponse(
                message=result["message"],
                products=result["products"],
                intent=intent,
                comparison_table=result.get("comparison_table"),
            )
        if last_products:
            message = (
                "Which of these would you like to compare? "
                "You can say 'the first two' or name specific products."
            )
        else:
            message = (
                "I'd be happy to compare products! "
                "Share 2–3 product names or paste their links from our site."
            )
        return OrchestratorResponse(
            message=message,
            products=[],
            intent=intent,
            comparison_table=None,
        )

    if intent["intent_type"] == "refinement" and recent_recs:
        keywords = intent.get("keywords") or []
        # Fallback: derive keywords from user feedback when intent classifier returns none
        if not keywords:
            fb_lower = (user_message or "").strip().lower()
            for pattern, additions in REFINEMENT_SEARCH_ADDITIONS.items():
                if pattern in fb_lower:
                    keywords = [pattern] + additions
                    break
            if not keywords:
                keywords = [w for w in fb_lower.split() if len(w) > 2][:3] or ["gift"]
        result = get_recommendations(
            keywords,
            last_search_query or user_message,
            previous_products=last_products,
            user_feedback=user_message,
            original_request=last_search_query,
            debug=debug,
        )
        resp: dict = {
            "message": result["message"],
            "products": result["products"],
            "intent": intent,
            "comparison_table": None,
        }
        if result.get("debug_llm_response"):
            resp["debug_llm_response"] = result["debug_llm_response"]
        return resp

    if intent["intent_type"] in ("search", "clarify") and intent["keywords"]:
        result = get_recommendations(
            intent["keywords"],
            user_message,
            debug=debug,
        )
        resp = {
            "message": result["message"],
            "products": result["products"],
            "intent": intent,
            "comparison_table": None,
        }
        if result.get("debug_llm_response"):
            resp["debug_llm_response"] = result["debug_llm_response"]
        return resp

    # Fallback: no keywords, not vague
    message = (
        "I'd be happy to help you find a gift! Could you tell me more? "
        "For example: the occasion (birthday, anniversary), who it's for, or your budget."
    )
    return OrchestratorResponse(
        message=message,
        products=[],
        intent=intent,
        comparison_table=None,
    )
