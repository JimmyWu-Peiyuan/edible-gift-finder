"""Flask app for AI-powered product discovery."""

import json
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

POPULAR_PRODUCTS_PATH = PROJECT_ROOT / "data" / "popular_products.json"

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


def _load_popular_products() -> list[dict]:
    """Load popular products from local JSON file. Returns empty list if missing or invalid."""
    if not POPULAR_PRODUCTS_PATH.exists():
        return []
    try:
        data = json.loads(POPULAR_PRODUCTS_PATH.read_text())
        return data.get("products", [])
    except (json.JSONDecodeError, OSError):
        return []


def _save_popular_products(products: list[dict]) -> None:
    """Save popular products to local JSON file."""
    POPULAR_PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    POPULAR_PRODUCTS_PATH.write_text(json.dumps({"products": products}, indent=2))


@app.route("/")
def index():
    """Serve the chat UI."""
    return render_template("index.html")


@app.route("/api/popular")
def popular():
    """Return popular/featured products for the shelf. Loads from local file; fetches and saves if empty."""
    try:
        products = _load_popular_products()
        if not products:
            from app.service.edible_client import EdibleAPIClient

            client = EdibleAPIClient()
            results = client.search_multiple(["birthday", "chocolate strawberries", "gift"])
            products = results.get("products", [])[:6]
            for p in products:
                p.pop("_search_score", None)
            _save_popular_products(products)
        return jsonify({"products": products[3:]})
    except Exception as e:
        return jsonify({"products": [], "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """Process user message and return assistant response with optional products."""
    data = request.get_json() or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []
    last_products = data.get("last_products") or []
    last_search_query = (data.get("last_search_query") or "").strip() or None
    debug = bool(data.get("debug"))

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        from app.service.orchestrator import respond

        result = respond(
            user_message,
            history if history else None,
            last_products=last_products if last_products else None,
            last_search_query=last_search_query,
            debug=debug,
        )
        payload = {
            "message": result["message"],
            "products": result.get("products", []),
        }
        if result.get("comparison_table") is not None:
            payload["comparison_table"] = result["comparison_table"]
        if result.get("debug_llm_response") is not None:
            payload["debug_llm_response"] = result["debug_llm_response"]
        return jsonify(payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
