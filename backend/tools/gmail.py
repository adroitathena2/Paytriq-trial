"""Gmail helpers: classify, draft, and mock-send (no creds needed)."""
from __future__ import annotations

from typing import Dict, List

OUTBOX: List[Dict[str, str]] = []


def classify_reply(text: str) -> str:
    """Classify a brand reply into interested / pushback / yes / no."""
    t = (text or "").lower()
    if any(k in t for k in ("yes", "deal", "confirmed", "let's do it", "lets do it", "signed", "agree")):
        return "yes"
    if any(k in t for k in ("no budget", "not interested", "pass", "cannot", "can't", "no thanks")):
        return "no"
    if any(k in t for k in ("expensive", "too high", "discount", "budget", "reduce", "cheaper", "negotiat")):
        return "pushback"
    if any(k in t for k in ("interest", "tell me more", "share", "deck", "call", "meeting", "sounds good")):
        return "interested"
    return "interested" if t.strip() else "none"


def draft_followup(brand: str, day: int, context: str = "") -> Dict[str, str]:
    """Draft a day-3 / day-7 follow-up email."""
    day_label = {3: "quick nudge", 7: "final call"}.get(day, "follow-up")
    subject = f"Re: {brand} x Campus Fest — {day_label} (Day {day})"
    body = (
        f"Hi {brand} team,\n\nJust a {day_label} on our sponsorship deck. {context} "
        "We have 5000+ student footfall and can tailor logo placement + stall. "
        "Open to a 10-min call this week?\n\nThanks!"
    )
    return {"to": brand, "subject": subject, "body": body}


def send_email(to: str, subject: str, body: str, approve: bool = True) -> Dict[str, str]:
    """Mock send: if approve False return pending, else append to OUTBOX."""
    if not approve:
        return {"status": "pending", "to": to, "subject": subject}
    OUTBOX.append({"to": to, "subject": subject, "body": body})
    return {"status": "sent", "to": to, "subject": subject}
