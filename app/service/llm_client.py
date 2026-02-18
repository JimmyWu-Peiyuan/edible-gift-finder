"""Thin wrapper for LLM API calls. Uses OpenAI Responses API."""

import json
import os

import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get_client() -> OpenAI:
    """Return OpenAI client. Uses env OPENAI_API_KEY. Handles httpx 0.28+ compatibility."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Add it to .env or export it. "
            "Copy .env.example to .env and add your key."
        )
    try:
        return OpenAI()
    except TypeError as e:
        if "proxies" in str(e):
            http_client = httpx.Client(timeout=60.0, follow_redirects=True)
            return OpenAI(api_key=api_key, http_client=http_client)
        raise


def complete(
    system_prompt: str,
    user_message: str,
    *,
    model: str = "gpt-4o-mini",
    json_mode: bool = False,
) -> str:
    """
    Send a completion request using the Responses API. Return the assistant's text.
    """
    client = _get_client()
    # Responses API requires "json" in input when using json_object format
    input_text = f"{user_message}\n\nRespond with JSON." if json_mode else user_message
    kwargs = {
        "model": model,
        "instructions": system_prompt,
        "input": input_text,
    }
    if json_mode:
        kwargs["text"] = {"format": {"type": "json_object"}}

    response = client.responses.create(**kwargs)
    return response.output_text or ""


def complete_json(
    system_prompt: str, user_message: str, *, return_raw: bool = False, **kwargs
) -> dict | tuple[dict, str]:
    """Call complete with json_mode and parse the result. If return_raw=True, returns (data, raw_text)."""
    text = complete(system_prompt, user_message, json_mode=True, **kwargs)
    data = json.loads(text)
    if return_raw:
        return data, text
    return data
