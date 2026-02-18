#!/usr/bin/env python3
"""Test the intent classifier - Layer 1 of AI product discovery."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.service.intent_classifier import get_intent

TEST_QUERIES = [
    "I need a gift",
    "birthday gift under $50",
    "chocolate covered strawberries for my mom",
    "help me choose between the fruit bouquet and the chocolate box",
    "something sweet",
    "around 40 dollars",
]


def main():
    print("Intent Classifier - Layer 1 Test\n")
    print("=" * 60)

    for query in TEST_QUERIES:
        print(f"\nUser: {query}")
        try:
            intent = get_intent(query)
            print(f"  intent_type: {intent['intent_type']}")
            print(f"  keywords: {intent['keywords']}")
            print(f"  needs_followup: {intent['needs_followup']}")
            if intent.get("followup_reason"):
                print(f"  followup_reason: {intent['followup_reason']}")
            print(f"  comparison_requested: {intent['comparison_requested']}")
            print(f"  confidence: {intent['confidence']}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
