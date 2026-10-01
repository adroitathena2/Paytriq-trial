"""LLM helper with offline-safe fallback."""
from __future__ import annotations

import os


def llm_complete(prompt: str, system: str = "") -> str:
    """Complete a prompt via Gemini if key exists, else deterministic mock.

    Never raises for missing keys / no network; always returns a string.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            from google import genai  # type: ignore
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system}\n{prompt}" if system else prompt,
            )
            text = getattr(resp, "text", "") or str(resp)
            if text.strip():
                return text.strip()
        except Exception:
            pass  # fall through to mock
    # Deterministic mock: echo keywords so demos look contextual.
    words = prompt.split()
    keywords = " ".join(words[:14])
    prefix = f"[mock-llm] {system[:60]} | " if system else "[mock-llm] "
    return (
        f"{prefix}Draft based on: {keywords}... "
        "We would love to partner with you for our college fest "
        "(5000+ footfall, student audience). Reply for the full deck."
    )
