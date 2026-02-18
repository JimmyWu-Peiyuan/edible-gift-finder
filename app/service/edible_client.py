import json
import re
import requests
from typing import Optional
from urllib.parse import urlparse

SITE_BASE = "https://www.ediblearrangements.com"
FRUIT_GIFTS_PREFIX = f"{SITE_BASE}/fruit-gifts/"


def parse_product_url(url: str) -> str | None:
    """Extract product slug from ediblearrangements.com product URL. Returns None if not valid."""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if "/fruit-gifts/" in path:
            match = re.search(r"/fruit-gifts/([^/?]+)", path)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def _normalize_product(p: dict) -> dict:
    """Extract display-ready fields from API product."""
    url_slug = p.get("url") or ""
    return {
        "id": p.get("id") or p.get("number"),
        "name": p.get("name", ""),
        "price": p.get("minPrice") or p.get("maxPrice") or p.get("price"),
        "url": f"{SITE_BASE}/fruit-gifts/{url_slug}" if url_slug else "",
        "image_url": p.get("image") or p.get("thumbnail") or "",
        "description": (p.get("description") or "")[:500],
        "occasion": p.get("occasion") or "",
        "category": (p.get("category") or "")[:200],
        "ingredients": (p.get("ingrediantNames") or "")[:300],
        "size_count": p.get("sizeCount"),
        "allergy_info": (p.get("allergyinformation") or "")[:200],
        "_search_score": p.get("@search.score"),
    }


class EdibleAPIClient:
    BASE_URL = "https://www.ediblearrangements.com/api/search/"
    
    HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    
    def search_raw(self, keyword: str) -> dict | list:
        """Fetch raw API response (no normalization, no limit)."""
        response = requests.post(
            self.BASE_URL,
            json={"keyword": keyword},
            headers=self.HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def search(self, keyword: str, limit: Optional[int] = None) -> dict:
        """
        Search Edible Arrangements catalog by keyword.
        """
        payload = {"keyword": keyword}
        
        response = requests.post(
            self.BASE_URL,
            json=payload,
            headers=self.HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, list):
            products = data
        else:
            products = data.get("products", [])
        
        if limit:
            products = products[:limit]

        return {"products": [_normalize_product(p) for p in products]}
    
    def search_multiple(self, keywords: list[str]) -> dict:
        """Search multiple keywords and combine results (deduplicated by id)."""
        all_products = {}
        for kw in keywords:
            for p in self.search(kw).get("products", []):
                pid = p.get("id")
                if pid and pid not in all_products:
                    all_products[pid] = p
        return {"products": list(all_products.values())}
    
    def lookup_by_name(self, product_name: str) -> dict | None:
        """Search by product name, return best match (highest relevance) or None."""
        if not product_name or not product_name.strip():
            return None
        result = self.search(product_name.strip(), limit=5)
        products = result.get("products", [])
        if not products:
            return None
        # Sort by search score descending, take best
        def _score(p: dict) -> float:
            s = p.get("_search_score")
            return float(s) if s is not None else 0.0

        best = max(products, key=_score)
        return best

    def lookup_by_url(self, url: str) -> dict | None:
        """Extract slug from URL, search by slug, return best match or None."""
        slug = parse_product_url(url)
        if not slug:
            return None
        return self.lookup_by_name(slug)

    def format_for_llm(self, products: list[dict]) -> str:
        """Format product data as context for LLM prompts (includes description for relevance)."""
        blocks = []
        for p in products:
            name = p.get("name", "Unknown")
            price = p.get("price", "N/A")
            desc = (p.get("description") or "").strip()
            occasion = (p.get("occasion") or "").strip()
            block = [f"- {name} | ${price}"]
            if occasion:
                block.append(f"  Occasion: {occasion}")
            if desc:
                block.append(f"  {desc}")
            blocks.append("\n".join(block))
        return "\n\n".join(blocks)

    def format_for_comparison(self, products: list[dict]) -> str:
        """Format product metadata for LLM comparison prompt."""
        blocks = []
        for p in products:
            name = p.get("name", "Unknown")
            price = p.get("price", "N/A")
            price_str = f"${float(price):.2f}" if isinstance(price, (int, float)) else str(price)
            parts = [
                f"**{name}**",
                f"Price: {price_str}",
                f"Occasion: {p.get('occasion') or 'N/A'}",
                f"Description: {(p.get('description') or '')[:300]}",
                f"Ingredients: {(p.get('ingredients') or 'N/A')[:200]}",
                f"Size options: {p.get('size_count', 'N/A')}",
            ]
            if p.get("allergy_info"):
                parts.append(f"Allergies: {p['allergy_info'][:150]}")
            blocks.append("\n".join(parts))
        return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    import sys

    client = EdibleAPIClient()

    if len(sys.argv) > 1 and sys.argv[1] == "--raw":
        # Raw API response for testing
        raw = client.search_raw(sys.argv[2] if len(sys.argv) > 2 else "birthday")
        print(json.dumps(raw, indent=2)[:5000])
        if len(json.dumps(raw)) > 5000:
            print("\n... (truncated, full response in raw variable)")
    else:
        results = client.search("birthday", limit=3)
        products = results["products"]
        print(f"Found {len(products)} products\n")
        for p in products:
            print(f"{p['name']} | ${p['price']}")
            print(f"  URL: {p['url']}")
            img = p.get("image_url", "")
            print(f"  Image: {img[:80]}{'...' if len(img) > 80 else ''}")