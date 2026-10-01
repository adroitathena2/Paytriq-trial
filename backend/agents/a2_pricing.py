"""A2 Pricing: tiered proposals + pushback revision."""
from __future__ import annotations

from typing import Dict, List

from ..state import BrandLead, EventProfile, Proposal
from ..tools.llm import llm_complete

TIERS: Dict[str, Dict[str, object]] = {
    "Title Sponsor": {"amount": 25000, "deliverables": ["main banner", "stage shoutout", "stall", "social posts"]},
    "Co-Sponsor": {"amount": 15000, "deliverables": ["side banner", "stall", "social post"]},
    "Stall Only": {"amount": 7000, "deliverables": ["stall", "flyer insert"]},
}


def pick_tier(brand: BrandLead, event: EventProfile) -> str:
    """Pick tier by fit + footfall."""
    if brand.fit_score >= 85 and event.footfall >= 4000:
        return "Title Sponsor"
    if brand.fit_score >= 70:
        return "Co-Sponsor"
    return "Stall Only"


def make_proposal(event: EventProfile, brand: BrandLead) -> Proposal:
    """Build 3-tier-aware proposal with LLM cover letter."""
    tier = pick_tier(brand, event)
    cfg = TIERS[tier]
    letter = llm_complete(
        f"Cover letter: invite {brand.name} as {tier} for {event.name} ({event.footfall} footfall).",
        system="You write sponsor cover letters.")
    return Proposal(brand=brand.name, tier=tier, amount=int(cfg["amount"]),
                    deliverables=list(cfg["deliverables"]), cover_letter=letter)  # type: ignore


def revise_for_pushback(proposal: Proposal, constraint: str = "budget") -> Proposal:
    """Create a micro-tier: drop priciest deliverable, halve price."""
    keep = [d for d in proposal.deliverables if "banner" not in d.lower()][:3] or proposal.deliverables[:2]
    if "social post" not in " ".join(keep).lower():
        keep = keep + ["social post"]
    return Proposal(brand=proposal.brand, tier=f"{proposal.tier} (Micro)",
                    amount=max(3000, proposal.amount // 2),
                    deliverables=keep,
                    cover_letter=f"Revised for {constraint}: leaner package at half price. " + proposal.cover_letter[:200])
