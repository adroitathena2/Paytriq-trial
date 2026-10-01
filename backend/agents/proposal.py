"""A2 Proposal generator. Offline tiered pricing + deliverables."""
from __future__ import annotations
from typing import Any, Dict, List


def _tier_for_score(score: float) -> tuple[str, float]:
    if score >= 80:
        return ("Title Sponsor", 1.0)
    if score >= 68:
        return ("Gold Sponsor", 0.6)
    return ("Silver Sponsor", 0.35)


def propose(event: Dict[str, Any], brand_names: List[str] | None = None) -> List[Dict[str, Any]]:
    footfall = int(event.get("footfall", 0) or 0)
    event_name = str(event.get("name", "Campus Event"))
    location = str(event.get("location", ""))
    discovery = event.get("discovery", []) or []
    score_by_brand = {d.get("brand"): d.get("fit_score", 60) for d in discovery}

    if not brand_names:
        # default: top 3 by fit-score, or fallback brands if discovery empty
        if discovery:
            brand_names = [d["brand"] for d in discovery[:3]]
        else:
            brand_names = ["boAt", "Red Bull", "Swiggy"]

    base_rate = 12.0  # Rs per head of footfall for Title tier (heuristic)
    proposals: List[Dict[str, Any]] = []
    for brand in brand_names:
        score = float(score_by_brand.get(brand, 65))
        tier, mult = _tier_for_score(score)
        amount = round(footfall * base_rate * mult, -2)  # round to 100s
        amount = max(amount, 5000)
        if tier == "Title Sponsor":
            deliverables = [
                f"Main-stage branding + naming: '{brand} presents {event_name}'",
                "Logo on all posters, lanyards & certificates",
                f"10x10 stall in high-footfall zone ({location or 'venue'})",
                "5-min keynote slot + product demo booth",
                "Instagram reels (3) + story mentions + email blast",
            ]
        elif tier == "Gold Sponsor":
            deliverables = [
                "Stage side-panel branding + MC shoutouts",
                "Logo on posters & event website",
                "8x8 stall + sampling permission",
                "1 Instagram reel + stories + push notification",
            ]
        else:
            deliverables = [
                "Logo on website & thank-you slide",
                "6x6 stall",
                "Social media story mention",
            ]
        proposals.append(
            {
                "brand": brand,
                "tier": tier,
                "amount_inr": amount,
                "fit_score": score,
                "deliverables": deliverables,
                "pitch": (
                    f"Dear {brand} team, {event_name} ({location}) expects {footfall} footfall. "
                    f"As {tier} at Rs {amount:,.0f}, you get: {'; '.join(deliverables[:3])}. "
                    "Campus audiences convert 2-4% on sampling + QR offers."
                ),
            }
        )
    return proposals


def revise_proposal(proposal: Dict[str, Any], feedback: str) -> Dict[str, Any]:
    """Apply pushback feedback: discount 10-20% + extra deliverable. Offline."""
    import copy

    revised = copy.deepcopy(proposal)
    fb = (feedback or "").lower()
    discount = 0.15 if any(w in fb for w in ["expensive", "too high", "budget", "reduce"]) else 0.10
    old = float(revised.get("amount_inr", 0) or 0)
    revised["amount_inr"] = round(old * (1 - discount), -2)
    revised["revision_note"] = f"Discounted {int(discount*100)}% from Rs {old:,.0f} after sponsor pushback."
    dl = revised.get("deliverables", [])
    if "Extra: logo on entry archway" not in dl:
        dl.append("Extra: logo on entry archway (goodwill add-on)")
    revised["deliverables"] = dl
    revised["revised"] = True
    return revised
