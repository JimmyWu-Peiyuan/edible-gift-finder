"""Side-by-Side AI Comparison Engine."""

from typing import TypedDict

from app.prompts.comparison import COMPARISON_SYSTEM
from app.service.edible_client import EdibleAPIClient
from app.service.llm_client import complete_json


class ComparisonResult(TypedDict):
    """Result of comparison flow."""

    message: str
    products: list[dict]
    comparison_table: list[dict] | None


def _is_url(s: str) -> bool:
    """Check if string looks like a URL."""
    s = (s or "").strip()
    return s.startswith(("http://", "https://")) or "ediblearrangements.com" in s


def _match_product_from_last(
    item: str, last_products: list[dict]
) -> dict | None:
    """Match item (name or ordinal) against last_products. Returns product or None."""
    if not last_products:
        return None
    item_lower = (item or "").strip().lower()
    # Ordinals: "first", "second", "1st", "2nd", "first two" (take first two)
    if item_lower in ("first", "1st", "1"):
        return last_products[0] if last_products else None
    if item_lower in ("second", "2nd", "2"):
        return last_products[1] if len(last_products) > 1 else None
    if item_lower in ("third", "3rd", "3"):
        return last_products[2] if len(last_products) > 2 else None
    # Match by name (fuzzy - contains)
    for p in last_products:
        name = (p.get("name") or "").strip().lower()
        if item_lower in name or name in item_lower:
            return p
    return None


def _expand_ordinals(
    products_to_compare: list[str], last_products: list[dict]
) -> list[str]:
    """Expand 'first two' etc. into product names. Returns list of names or URLs."""
    expanded = []
    for item in products_to_compare:
        item = (item or "").strip()
        if not item:
            continue
        item_lower = item.lower()
        if "first two" in item_lower or "first 2" in item_lower:
            expanded.extend(
                (p.get("name") or "") for p in last_products[:2] if p.get("name")
            )
        elif "first three" in item_lower or "first 3" in item_lower:
            expanded.extend(
                (p.get("name") or "") for p in last_products[:3] if p.get("name")
            )
        else:
            expanded.append(item)
    return [x for x in expanded if x]


def get_comparison(
    products_to_compare: list[str],
    last_products: list[dict] | None = None,
) -> ComparisonResult:
    """
    Resolve products and generate AI comparison table.

    products_to_compare: Product names, URLs, or ordinals ("first two")
    last_products: Recently shown products (for "compare these" flow)
    """
    if not products_to_compare:
        return ComparisonResult(
            message="Which products would you like to compare? Share 2-3 product names or paste their links.",
            products=[],
            comparison_table=None,
        )

    client = EdibleAPIClient()
    last_products = last_products or []

    # Expand ordinals like "first two" into product names
    items = _expand_ordinals(products_to_compare, last_products)
    if not items:
        items = list(products_to_compare)

    resolved: list[dict] = []
    seen_ids: set[str] = set()

    for item in items[:5]:  # Cap at 5, we'll take 3
        if len(resolved) >= 3:
            break
        item = (item or "").strip()
        if not item:
            continue

        # 1. Try last_products first (by name or ordinal)
        if last_products:
            p = _match_product_from_last(item, last_products)
            if p:
                pid = str(p.get("id") or p.get("name", ""))
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    resolved.append(p)
                continue

        # 2. Try URL lookup
        if _is_url(item):
            p = client.lookup_by_url(item)
            if p:
                pid = str(p.get("id") or p.get("name", ""))
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    resolved.append(p)
            continue

        # 3. Search by name
        p = client.lookup_by_name(item)
        if p:
            pid = str(p.get("id") or p.get("name", ""))
            if pid not in seen_ids:
                seen_ids.add(pid)
                resolved.append(p)

    if len(resolved) < 2:
        if len(resolved) == 1:
            return ComparisonResult(
                message="I found one product. Please specify at least one more to compare.",
                products=resolved,
                comparison_table=None,
            )
        not_found = items[0] if items else "those"
        return ComparisonResult(
            message=f"I couldn't find '{not_found}' in our catalog. Try searching for it first, then compare.",
            products=[],
            comparison_table=None,
        )

    products = resolved[:3]
    product_context = client.format_for_comparison(products)

    user_content = f"""Compare these products and create a side-by-side comparison:

{product_context}

Return JSON with intro_message, comparison_rows, and best_for."""

    try:
        data = complete_json(COMPARISON_SYSTEM, user_content)
        rows = data.get("comparison_rows") or []
        best_for = data.get("best_for") or []

        # Build comparison_table for frontend: list of {attribute, values}
        comparison_table = []
        for r in rows:
            if isinstance(r, dict) and r.get("attribute"):
                comparison_table.append({
                    "attribute": r["attribute"],
                    "values": r.get("values") or [],
                })
        # Add Best For row
        if best_for:
            verdicts = []
            for p in products:
                name = p.get("name", "")
                v = next((b.get("verdict", "") for b in best_for if (b.get("product_name") or "").strip().lower() == name.strip().lower()), "")
                verdicts.append(v or "")
            comparison_table.append({"attribute": "Best For", "values": verdicts})

        intro = (data.get("intro_message") or "").strip()
        message = intro or f"Here's how these compare: {', '.join(p.get('name', '?') for p in products)}"

        # Strip internal fields before returning to frontend
        clean_products = []
        for p in products:
            cp = dict(p)
            cp.pop("_search_score", None)
            clean_products.append(cp)

        return ComparisonResult(
            message=message,
            products=clean_products,
            comparison_table=comparison_table,
        )
    except Exception:
        return ComparisonResult(
            message="I had trouble generating the comparison. Please try again.",
            products=products,
            comparison_table=None,
        )
