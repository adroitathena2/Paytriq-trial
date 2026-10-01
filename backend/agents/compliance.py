"""A5 Compliance checker. Rule-based, offline."""
from __future__ import annotations
from typing import Any, Dict, List


REQUIRED_TERMS_KEYWORDS = ["payment", "logo", "cancellation"]


def check_compliance(event: Dict[str, Any], mou: Dict[str, Any] | None = None) -> Dict[str, Any]:
    issues: List[str] = []
    if not mou:
        mous = event.get("mous", []) or []
        mou = mous[-1] if mous else None
    if not mou:
        return {"passed": False, "score": 0, "issues": ["no MoU found — generate one first"], "brand": None}

    brand = mou.get("brand")
    amount = float(mou.get("amount_inr", 0) or 0)
    if amount <= 0:
        issues.append("amount must be > 0")
    if amount > 1_000_000:
        issues.append("amount > Rs 10L needs faculty approval (flagged, not failed)")

    terms = str(mou.get("terms", "")).lower()
    for kw in REQUIRED_TERMS_KEYWORDS:
        if kw not in terms:
            issues.append(f"terms missing '{kw}' clause")

    if not mou.get("deliverables"):
        issues.append("no deliverables listed")

    if not event.get("name") or not mou.get("event"):
        issues.append("event name missing in MoU")

    # logo misuse heuristic: Title tier must include archway/main-stage mention
    proposals = event.get("proposals", []) or []
    match = next((p for p in proposals if p.get("brand") == brand), None)
    if match and match.get("tier") == "Title Sponsor":
        dl_text = " ".join(match.get("deliverables", [])).lower()
        if "main-stage" not in dl_text and "main stage" not in dl_text:
            issues.append("Title tier should include main-stage branding")

    score = max(0, 100 - len(issues) * 20)
    return {
        "passed": len([i for i in issues if "faculty approval" not in i]) == 0,
        "score": score,
        "issues": issues,
        "brand": brand,
        "mou_id": mou.get("mou_id"),
    }
