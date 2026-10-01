"""URL logo checker: mock + optional Playwright hook."""
from __future__ import annotations

from typing import Dict


def check_url_for_logo(url: str, promise: str) -> Dict[str, object]:
    """Mock check whether a brand logo/promise appears at url.

    Tries Playwright if installed; otherwise keyword heuristic.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        with sync_playwright() as p:  # pragma: no cover - needs browser
            b = p.chromium.launch(headless=True)
            pg = b.new_page()
            pg.goto(url, timeout=8000)
            html = pg.content().lower()
            b.close()
            key = promise.split()[0].lower() if promise else "logo"
            return {"found": key in html, "screenshot_note": f"playwright fetched {url}"}
    except Exception:
        pass
    keywords = [w.lower() for w in promise.split() if len(w) > 3]
    found = any(k in url.lower() for k in keywords) or "sponsor" in url.lower()
    return {"found": found, "screenshot_note": f"mock check of {url} for '{promise}'"}
