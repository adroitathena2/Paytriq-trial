"""A5 Compliance: verify signed terms vs live URLs/photos."""
from __future__ import annotations

from typing import Dict, List

from ..tools.browser import check_url_for_logo


def check_compliance(signed_terms: List[str], urls: List[str]) -> List[Dict[str, object]]:
    """Check each promise against urls; flag nudges for missing ones."""
    results = []
    for promise in signed_terms:
        found = any(bool(check_url_for_logo(u, promise).get("found")) for u in urls) if urls else False
        results.append({"promise": promise, "found": found, "nudge_needed": not found})
    return results


def nudge_text(missing: List[str]) -> Dict[str, str]:
    """Draft WhatsApp + email nudge for missing deliverables."""
    items = ", ".join(missing) if missing else "all deliverables"
    return {
        "whatsapp": f"Hi! Quick reminder: {items} still pending from our MoU. Could you post by EOD?",
        "email_subject": "Pending sponsor deliverables — quick nudge",
        "email_body": f"Hello,\n\nAs per our MoU, {items} are still pending. Please share at the earliest.\n\nThanks!",
    }
