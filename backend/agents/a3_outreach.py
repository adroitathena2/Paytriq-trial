"""A3 Outreach: day-0/3/7 sends + reply handling."""
from __future__ import annotations

from typing import Dict

from ..state import OutreachThread
from ..tools.gmail import classify_reply, draft_followup, send_email


def send_day0(brand: str, email: str, cover_letter: str, approve: bool = True) -> OutreachThread:
    """Send initial pitch."""
    send_email(email or brand, f"{brand} x Campus Fest — Sponsorship", cover_letter, approve=approve)
    return OutreachThread(brand=brand, email=email, day=0, status="sent")


def followup_day3(thread: OutreachThread, approve: bool = True) -> OutreachThread:
    """Send day-3 nudge."""
    d = draft_followup(thread.brand, 3, "Slots filling fast.")
    send_email(thread.email or thread.brand, d["subject"], d["body"], approve=approve)
    thread.day = 3
    thread.status = "followed_up_3"
    return thread


def followup_day7(thread: OutreachThread, approve: bool = True) -> OutreachThread:
    """Send day-7 final call."""
    d = draft_followup(thread.brand, 7, "Last call before print deadline.")
    send_email(thread.email or thread.brand, d["subject"], d["body"], approve=approve)
    thread.day = 7
    thread.status = "followed_up_7"
    return thread


def handle_reply(thread_text: str) -> Dict[str, str]:
    """Classify reply text -> intent + next action."""
    intent = classify_reply(thread_text)
    nxt = {"yes": "route_to_contract", "pushback": "route_to_repricing",
           "interested": "send_deck_and_call", "no": "archive"}.get(intent, "followup")
    return {"intent": intent, "next_action": nxt}
