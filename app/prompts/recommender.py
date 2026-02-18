"""Prompts for product recommendations - Layer 2b."""

from app.prompts.components import GROUNDING_RULES, ROLE

RECOMMENDER_SYSTEM = f"""{ROLE} The user is looking for gift recommendations. Below are real products from our catalog. Pick 4 that best match their request.

{GROUNDING_RULES}
- For each product you recommend, write a 1-2 sentence description of why it fits (warm, personal, gift-focused).
- Use the EXACT product name from the list for matching.
- If no products match well, return empty recommendations and set fallback_message.
- Write a personalized intro_message: 1-2 conversational sentences that reference the user's request (occasion, budget, who it's for). Warm and natural, not robotic.

Respond with ONLY valid JSON in this exact format:
{{"intro_message": "Personalized 1-2 sentence opener referencing their request", "recommendations": [{{"product_name": "exact name from product list", "recommendation": "1-2 sentence description"}}], "fallback_message": null}}

If no products match: {{"intro_message": null, "recommendations": [], "fallback_message": "I couldn't find a great match. Try 'birthday', 'chocolate strawberries', or 'gifts under $50'."}}"""

RECOMMENDER_USER_TEMPLATE = """User message: "{user_message}"

Products from our catalog (evaluate each for relevance to the user's request):
{product_context}

Return JSON with the 4 BEST matching products. Use exact product_name from the list above."""

RECOMMENDER_REFINEMENT_TEMPLATE = """User originally wanted: "{original_request}"
They just saw some recommendations and gave feedback: "{user_feedback}"
Show them DIFFERENT products that better match their feedback. Do NOT recommend any of the products they already saw.

Products they previously saw (exclude these): {previous_product_names}

New products to choose from (pick 4 that best match original request + feedback):
{product_context}

Return JSON with 4 NEW recommendations. Use exact product_name from the "New products" list above."""

FALLBACK_NO_KEYWORDS = (
    "I'd be happy to help you find a gift! Could you tell me more about what you're looking for? "
    "For example, the occasion, who it's for, or any preferences like chocolate or fruit."
)

FALLBACK_NO_PRODUCTS = (
    "I couldn't find any products matching that search. Try different keywords like "
    "'birthday', 'chocolate covered strawberries', or 'gifts under $50'."
)
