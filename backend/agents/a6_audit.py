"""A6 Audit: ROI report + learning update for A1 feedback."""
from __future__ import annotations

from typing import Dict, List

from ..state import Deliverable, EventProfile, OutreachThread
from ..tools.pdf import make_roi_pdf
from ..tools.vision import audit_deliverables, count_logos


def build_roi(event: EventProfile, deliverables: List[Deliverable], photos: List[str],
              links: List[str], threads: List[OutreachThread],
              out_path: str = "out/roi.pdf") -> Dict[str, object]:
    """Combine vision + thread stats into ROI dict and PDF."""
    promises = [d.promise for d in deliverables]
    audit = audit_deliverables(promises, photos, links)
    footfall = sum(int(count_logos(p).get("footfall_estimate", 0)) for p in photos) if photos else event.footfall
    yes = sum(1 for t in threads if t.intent == "yes")
    roi = {"event": event.name, "compliance_pct": audit["compliance_pct"],
           "findings": audit["findings"], "footfall_estimate": footfall,
           "deals_closed": yes, "threads": len(threads)}
    roi["pdf_path"] = make_roi_pdf({k: v for k, v in roi.items() if k != "findings"}, out_path)
    return roi


def learning_update(roi: Dict[str, object]) -> Dict[str, object]:
    """Summarise converting categories + weight delta for A1 re-tuning."""
    pct = float(roi.get("compliance_pct", 0))
    delta = 0.05 if pct >= 80 else (-0.05 if pct < 50 else 0.0)
    return {"converting_categories": ["cafe", "coaching"] if pct >= 50 else ["gym"],
            "weight_delta": delta,
            "note": f"compliance {pct}% -> adjust category weights by {delta}"}
