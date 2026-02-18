#!/usr/bin/env python3
"""Test Layer 2 - Response layer (follow-up, recommendations, orchestrator)."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.service.orchestrator import respond

TEST_QUERIES = [
    "I need a gift",
    "birthday gift under $50",
    "chocolate covered strawberries for my mom",
]


def main():
    print("Layer 2 - Orchestrator Test\n")
    print("=" * 60)

    for query in TEST_QUERIES:
        print(f"\nUser: {query}")
        try:
            result = respond(query)
            msg = result["message"]
            print(f"Assistant: {msg[:300]}{'...' if len(msg) > 300 else ''}")
            if result["products"]:
                print(f"  Products: {len(result['products'])} returned")
                for p in result["products"][:3]:
                    print(f"    - {p['name']} | ${p.get('price', 'N/A')}")
            print(f"  Intent: {result['intent']['intent_type']}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
