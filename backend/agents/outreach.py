"""A3 Outreach: human-gated send. Writes .txt to outbox/, never needs SMTP."""
from __future__ import annotations
import os
import time
from typing import Any, Dict, List

OUTBOX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outbox")


def send_outreach(event: Dict[str, Any], brand_names: List[str] | None = None) -> Dict[str, Any]:
    proposals = event.get("proposals", []) or []
    if brand_names:
        wanted = set(brand_names)
        targets = [p for p in proposals if p.get("brand") in wanted]
        missing = [b for b in brand_names if b not in {p.get("brand") for p in targets}]
    else:
        targets = proposals
        missing = []

    sent: List[Dict[str, Any]] = []
    errors: List[str] = []
    try:
        os.makedirs(OUTBOX_DIR, exist_ok=True)
    except Exception as e:  # noqa: BLE001
        errors.append(f"outbox mkdir failed: {e}")

    for p in targets:
        brand = p.get("brand", "Unknown")
        subject = f"Sponsorship Proposal: {event.get('name')} x {brand} ({p.get('tier')})"
        body = p.get("pitch", "") + f"\n\nAmount: Rs {p.get('amount_inr', 0):,.0f}\nDeliverables:\n- " + "\n- ".join(
            p.get("deliverables", [])
        )
        record = {
            "brand": brand,
            "subject": subject,
            "body": body,
            "sent_at": time.time(),
            "status": "sent",
        }
        # best-effort file write; failure must not crash send
        try:
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in brand)[:40]
            fname = f"{event.get('event_id','evt')}_{safe}.txt"
            with open(os.path.join(OUTBOX_DIR, fname), "w", encoding="utf-8") as f:
                f.write(f"To: partnerships@{safe.lower()}.com\nSubject: {subject}\n\n{body}\n")
            record["file"] = fname
        except Exception as e:  # noqa: BLE001
            errors.append(f"file write failed for {brand}: {e}")
        sent.append(record)

    for b in missing:
        errors.append(f"no proposal found for brand '{b}' — run /api/propose first")

    return {"sent": sent, "errors": errors, "count": len(sent)}
