"""A1 Discovery: rank sponsor brands by fit-score. Fully offline heuristic."""
from __future__ import annotations
from typing import Any, Dict, List

BRAND_POOL = [
    {"brand": "boAt", "category": "audio/wearables", "keywords": ["tech", "fest", "music", "youth", "concert"]},
    {"brand": "Red Bull", "category": "beverage/energy", "keywords": ["sports", "fest", "music", "tech", "cultural"]},
    {"brand": "Swiggy", "category": "food-delivery", "keywords": ["food", "fest", "cultural", "youth", "campus"]},
    {"brand": "Zomato", "category": "food-delivery", "keywords": ["food", "fest", "cultural", "campus"]},
    {"brand": "HDFC Bank", "category": "banking/fintech", "keywords": ["finance", "tech", "startup", "summit", "expo"]},
    {"brand": "Jio", "category": "telecom", "keywords": ["tech", "fest", "summit", "hackathon", "expo"]},
    {"brand": "Coca-Cola", "category": "beverage", "keywords": ["cultural", "sports", "music", "fest", "food"]},
    {"brand": "Mamaearth", "category": "D2C/beauty", "keywords": ["lifestyle", "cultural", "youth", "expo", "fashion"]},
    {"brand": "Noise", "category": "wearables", "keywords": ["tech", "hackathon", "sports", "fest", "summit"]},
    {"brand": "Airtel", "category": "telecom", "keywords": ["tech", "gaming", "esports", "summit", "hackathon"]},
    {"brand": "Pepsi", "category": "beverage", "keywords": ["sports", "music", "cultural", "food"]},
    {"brand": "Devfolio", "category": "dev-tools", "keywords": ["hackathon", "tech", "coding", "summit"]},
]


def discover(event: Dict[str, Any], top_k: int = 8) -> List[Dict[str, Any]]:
    name = str(event.get("name", "")).lower()
    footfall = int(event.get("footfall", 0) or 0)
    audience = str(event.get("audience", "")).lower()

    # footfall bonus: bigger events attract bigger sponsors
    if footfall >= 5000:
        size_bonus = 10
    elif footfall >= 1000:
        size_bonus = 5
    else:
        size_bonus = 0

    scored = []
    for b in BRAND_POOL:
        hits = sum(1 for kw in b["keywords"] if kw in name or kw in audience)
        base = 55 + min(hits * 12, 36) + size_bonus
        # small deterministic jitter from brand name length so ordering is stable
        jitter = (len(b["brand"]) % 5) - 2  # -2..+2
        score = max(40, min(98, base + jitter))
        reason = (
            f"{hits} keyword match(es) ({', '.join([k for k in b['keywords'] if k in name or k in audience]) or 'general youth fit'}); "
            f"footfall={footfall} bonus +{size_bonus}"
        )
        scored.append(
            {
                "brand": b["brand"],
                "category": b["category"],
                "fit_score": score,
                "reason": reason,
            }
        )
    scored.sort(key=lambda x: x["fit_score"], reverse=True)
    return scored[:top_k]
