"""A1 Discovery: rank local brands by fit_score + LLM icebreaker."""
from __future__ import annotations

from typing import List

from ..state import BrandLead, EventProfile
from ..tools.llm import llm_complete
from ..tools.maps import fit_score, search_brands


def run_discovery(event: EventProfile, min_fit: float = 60.0) -> List[BrandLead]:
    """Search cached brands, score, filter fit>=min_fit, attach why/icebreaker."""
    raw = search_brands(event.location)
    leads: List[BrandLead] = []
    for b in raw:
        score = fit_score(event, b)
        if score < min_fit:
            continue
        name, cat = str(b["name"]), str(b["category"])
        why = f"{cat} near {event.location} ({b['distance_km']}km, {b['rating']}*), matches {event.audience}."
        ice = llm_complete(f"Write 1-line icebreaker for {name} ({cat}) sponsoring {event.name}.",
                           system="You write short sponsor outreach hooks.")
        leads.append(BrandLead(name=name, category=cat, distance_km=float(b["distance_km"]),
                               phone=str(b["phone"]), rating=float(b["rating"]),
                               fit_score=score, why_fit=why, icebreaker=ice))
    leads.sort(key=lambda l: l.fit_score, reverse=True)
    return leads
