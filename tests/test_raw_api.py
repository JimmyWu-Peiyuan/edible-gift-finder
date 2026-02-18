#!/usr/bin/env python3
"""Test script to inspect raw Edible API response."""

import json
from app.service.edible_client import EdibleAPIClient

client = EdibleAPIClient()

# Fetch raw response
keyword = "birthday"
raw = client.search_raw(keyword)

# Show structure
print(f"Response type: {type(raw).__name__}")
print(f"Length: {len(raw)} items\n")

# First item keys
if raw:
    first = raw[0] if isinstance(raw, list) else raw.get("products", [{}])[0]
    print("First item keys:", list(first.keys())[:20])
    print()

# Pretty-print first item (full)
print("--- First item (full) ---")
first_full = raw[0] if isinstance(raw, list) else raw.get("products", [{}])[0]
print(json.dumps(first_full, indent=2))

# Save full response to file for inspection
with open("raw_api_response.json", "w") as f:
    json.dump(raw, f, indent=2)
print("\nFull response saved to raw_api_response.json")
