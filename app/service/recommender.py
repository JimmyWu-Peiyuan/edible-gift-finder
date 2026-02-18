"""Search + grounded recommendations - Layer 2b."""

import re
from typing import TypedDict

from app.prompts.recommender import (
    FALLBACK_NO_KEYWORDS,
    FALLBACK_NO_PRODUCTS,
    RECOMMENDER_REFINEMENT_TEMPLATE,
    RECOMMENDER_SYSTEM,
    RECOMMENDER_USER_TEMPLATE,
)
from app.service.edible_client import EdibleAPIClient
from app.service.llm_client import complete_json

# this is used to fine-tune
MAX_RECOMMENDATIONS = 4
MAX_PRODUCTS_FOR_LLM = 15  # Limit context size


class RecommendationResult(TypedDict):
    """Result of recommendation flow."""

    message: str
    products: list[dict]


# Feedback keywords to expand search when user wants refinement
REFINEMENT_SEARCH_ADDITIONS: dict[str, list[str]] = {
    "cheaper": ["affordable", "gifts under $50"],
    "cheaper options": ["affordable", "gifts under $50"],
    "less expensive": ["affordable", "gifts under $50"],
    "more affordable": ["affordable", "gifts under $50"],
    "budget": ["affordable", "gifts under $50"],
    "more fun": ["birthday", "fun"],
    "something different": [],
    "different options": [],
    "other options": [],
    "more luxurious": ["luxury", "premium"],
    "fancier": ["luxury", "premium"],
    "for a kid": ["for kids", "kids"],
    "for kids": ["for kids", "kids"],
}


def get_recommendations(
    keywords: list[str],
    user_message: str,
    *,
    limit: int = MAX_RECOMMENDATIONS,
    previous_products: list[dict] | None = None,
    user_feedback: str | None = None,
    original_request: str | None = None,
    debug: bool = False,
) -> RecommendationResult:
    """
    Search catalog and generate grounded recommendations.

    Args:
        keywords: Search terms from intent classifier.
        user_message: Original user message (for context).
        limit: Max products to recommend in the response.
        previous_products: When user gave feedback, the products they saw before.
        user_feedback: User's feedback (e.g. "cheaper", "more fun").
        original_request: The user's original search query (for refinement context).

    Returns:
        RecommendationResult with message and products list.
    """
    if not keywords:
        return RecommendationResult(
            message=FALLBACK_NO_KEYWORDS,
            products=[],
        )

    is_refinement = bool(previous_products and user_feedback)

    # Add search terms for common feedback
    search_keywords = list(keywords)
    if is_refinement and user_feedback:
        fb_lower = user_feedback.strip().lower()
        for pattern, additions in REFINEMENT_SEARCH_ADDITIONS.items():
            if pattern in fb_lower:
                search_keywords.extend(additions)
                break

    client = EdibleAPIClient()
    results = client.search_multiple(search_keywords)
    products = results["products"]

    if not products:
        return RecommendationResult(
            message=FALLBACK_NO_PRODUCTS,
            products=[],
        )

    # Exclude previous products when refining
    previous_ids = {str(p.get("id")) for p in (previous_products or []) if p.get("id")}
    if previous_ids:
        products = [p for p in products if str(p.get("id")) not in previous_ids]
        if not products:
            return RecommendationResult(
                message="I've shown you the best matches for that search. Try different keywords like 'chocolate strawberries' or 'fruit bouquet' for more options.",
                products=[],
            )

    # Sort by API relevance (higher score = better match), then limit for LLM context
    def _score(p: dict) -> float:
        s = p.get("_search_score")
        return float(s) if s is not None else 0.0

    products_sorted = sorted(products, key=_score, reverse=True)
    products_for_context = products_sorted[:MAX_PRODUCTS_FOR_LLM]
    product_context = client.format_for_llm(products_for_context)

    if is_refinement:
        previous_names = ", ".join(p.get("name", "?") for p in previous_products[:8])
        user_content = RECOMMENDER_REFINEMENT_TEMPLATE.format(
            original_request=original_request or user_message,
            user_feedback=user_feedback,
            previous_product_names=previous_names,
            product_context=product_context,
        )
    else:
        user_content = RECOMMENDER_USER_TEMPLATE.format(
            user_message=user_message,
            product_context=product_context,
        )

    try:
        if debug:
            data, raw_text = complete_json(RECOMMENDER_SYSTEM, user_content, return_raw=True)
        else:
            data = complete_json(RECOMMENDER_SYSTEM, user_content)
            raw_text = None
        recs = data.get("recommendations") or []
        fallback = data.get("fallback_message")
    except Exception:
        data = None
        recs = []
        fallback = None
        raw_text = None

    # Build products in LLM recommendation order, with descriptions
    # Normalize names (strip ®, ™) so "Delicious Fruit Design" matches "Delicious Fruit Design®"
    def _norm(s: str) -> str:
        s = re.sub(r"[\u00ae\u2122]", "", (s or "").strip()).lower()
        # Strip " | $price" suffix that LLM may copy from format_for_llm
        s = re.sub(r"\s*\|\s*\$[\d.]+$", "", s).strip()
        return s

    name_to_product = {_norm(p.get("name", "")): p for p in products_for_context if _norm(p.get("name", ""))}
    products_with_recs = []
    seen = set()
    for r in recs:
        if len(products_with_recs) >= limit:
            break
        key = _norm(r.get("product_name") or "")
        if key in name_to_product and key not in seen:
            seen.add(key)
            p = dict(name_to_product[key])
            p.pop("_search_score", None)  # Internal only; don't expose to frontend
            products_with_recs.append({
                **p,
                "recommendation": r.get("recommendation") or "",
            })

    # Intro message: use LLM-generated intro when present, else fallback
    intro = (data or {}).get("intro_message") if data else None
    if products_with_recs:
        message = (intro or "").strip() or ("Here are some different options based on your feedback:" if is_refinement else "Here are my top picks for you:")
    elif fallback:
        message = (intro or "").strip() or fallback
        products_with_recs = []
    else:
        message = (intro or "").strip() or "I couldn't find a great match. Try different keywords?"
        products_with_recs = []

    result: dict = {"message": message, "products": products_with_recs}
    if debug and raw_text:
        result["debug_llm_response"] = raw_text
    return result
