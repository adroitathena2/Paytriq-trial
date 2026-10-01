"""A6 Audit / ROI + learning update. Offline arithmetic."""
from __future__ import annotations
import time
from typing import Any, Dict


def compute_roi(
    event: Dict[str, Any],
    actual_spend: float | None = None,
    actual_leads: int | None = None,
) -> Dict[str, Any]:
    footfall = int(event.get("footfall", 0) or 0)
    mous = event.get("mous", []) or []
    total_sponsored = round(sum(float(m.get("amount_inr", 0) or 0) for m in mous), 2)

    expected_leads = int(footfall * 0.03)  # 3% sampling conversion heuristic
    leads = int(actual_leads) if actual_leads is not None else expected_leads
    spend = float(actual_spend) if actual_spend is not None else round(total_sponsored * 0.15, 2)

    est_value_per_lead = 150.0
    pipeline_value = round(leads * est_value_per_lead, 2)
    denom = spend if spend > 0 else 1.0
    roi = round((pipeline_value + total_sponsored - spend) / denom, 3)

    return {
        "event_id": event.get("event_id"),
        "footfall": footfall,
        "total_sponsored_inr": total_sponsored,
        "leads": leads,
        "spend_inr": spend,
        "pipeline_value_inr": pipeline_value,
        "roi": roi,
        "computed_at": time.time(),
        "note": "Heuristic offline ROI: leads=3% footfall default; value Rs150/lead.",
    }
