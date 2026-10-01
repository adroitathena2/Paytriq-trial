"""Local brand search + fit scoring (offline, no API key required)."""
from __future__ import annotations

import os
from typing import Dict, List, Optional

# Static cache of 12 Pune businesses across 5 categories.
_CACHE: List[Dict[str, object]] = [
    {"name": "Cafe Brewo", "category": "cafe", "distance_km": 0.8, "phone": "+91-90001", "rating": 4.5},
    {"name": "Chai Sutta Corner", "category": "cafe", "distance_km": 1.2, "phone": "+91-90002", "rating": 4.2},
    {"name": "Bean & Brew", "category": "cafe", "distance_km": 2.5, "phone": "+91-90003", "rating": 4.0},
    {"name": "Iron Paradise Gym", "category": "gym", "distance_km": 0.5, "phone": "+91-90004", "rating": 4.6},
    {"name": "FitZone Studio", "category": "gym", "distance_km": 3.0, "phone": "+91-90005", "rating": 4.1},
    {"name": "Lakshya IAS Coaching", "category": "coaching", "distance_km": 1.0, "phone": "+91-90006", "rating": 4.4},
    {"name": "Vidyarthi Classes", "category": "coaching", "distance_km": 2.0, "phone": "+91-90007", "rating": 4.3},
    {"name": "GlowUp Salon", "category": "salon", "distance_km": 0.9, "phone": "+91-90008", "rating": 4.5},
    {"name": "StyleKart Unisex", "category": "salon", "distance_km": 2.2, "phone": "+91-90009", "rating": 3.9},
    {"name": "QuickPrint Hub", "category": "printing", "distance_km": 0.4, "phone": "+91-90010", "rating": 4.7},
    {"name": "Print Palace", "category": "printing", "distance_km": 1.8, "phone": "+91-90011", "rating": 4.0},
    {"name": "Campus Xerox Point", "category": "printing", "distance_km": 3.5, "phone": "+91-90012", "rating": 3.8},
]

# Category affinity for a student fest audience (0-1).
_CATEGORY_WEIGHT: Dict[str, float] = {
    "cafe": 1.0, "gym": 0.9, "coaching": 0.95, "salon": 0.8, "printing": 0.7,
}


def search_brands(location: str, category_filter: Optional[str] = None) -> List[Dict[str, object]]:
    """Return cached brands near location. Hook for Google Maps if key set.

    Args:
        location: free-text location, e.g. 'Pune'.
        category_filter: optional category to keep.
    """
    if os.getenv("GOOGLE_MAPS_KEY"):
        pass  # hook: replace _CACHE with live Places API call.
    rows = [dict(r, location=location) for r in _CACHE]
    if category_filter:
        rows = [r for r in rows if str(r["category"]).lower() == category_filter.lower()]
    return rows


def _as_dict(obj) -> Dict[str, object]:
    """Accept dicts or pydantic/objects; return plain dict."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()  # type: ignore
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            return dict(vars(obj))
        except Exception:
            pass
    return {}


def _is_event_like(d: Dict[str, object]) -> bool:
    return any(k in d for k in ("footfall", "event_name", "location", "audience_age", "audience"))


def fit_score(first, second=None, weights=None) -> float:
    """Weighted 0-100 fit: category30 + distance25 + budget25 + audience20.

    Accepts (brand, event) or (event, brand), dicts or models; never crashes.
    """
    a = _as_dict(first)
    b = _as_dict(second) if second is not None else {}
    if _is_event_like(a) and not _is_event_like(b) and b:
        event, brand = a, b  # called as (event, brand)
    elif _is_event_like(b) and not _is_event_like(a):
        event, brand = b, a  # called as (brand, event)
    elif _is_event_like(b):
        event, brand = b, a
    else:
        event, brand = b or {}, a
    cat = str(brand.get("category", "")).lower()
    evt_cat = str(event.get("category", "")).lower()
    if evt_cat and cat == evt_cat:
        category_pts = 30.0
    elif evt_cat:
        category_pts = 12.0  # mismatch penalty, still partly weighted
    else:
        category_pts = 30.0 * _CATEGORY_WEIGHT.get(cat, 0.5)
    try:
        dist = float(brand.get("distance_km", event.get("distance_km", 5.0)))  # type: ignore
    except (TypeError, ValueError):
        dist = 5.0
    distance_pts = max(0.0, 25.0 * (1.0 - min(dist, 1000.0) / 5.0)) if dist <= 5 else 0.0
    try:
        budget = float(brand.get("budget", brand.get("rating", 4.0)))  # type: ignore
    except (TypeError, ValueError):
        budget = 4.0
    budget_norm = budget / 5.0 if budget <= 5.0 else min(1.0, budget / 80000.0)
    budget_pts = 25.0 * max(0.0, min(1.0, budget_norm))
    try:
        footfall = int(event.get("footfall", getattr(first, "footfall", 5000)) or 0)
    except (TypeError, ValueError):
        footfall = 5000
    audience_pts = 20.0 if footfall >= 3000 else (12.0 if footfall >= 1000 else 6.0)
    try:
        am = float(brand.get("audience_match", 0.5))  # type: ignore
        audience_pts = max(0.0, min(20.0, audience_pts * (0.5 + am)))
    except (TypeError, ValueError):
        pass
    _ = weights  # reserved for learning-tuned weights
    return round(min(100.0, category_pts + distance_pts + budget_pts + audience_pts), 1)
