"""A4 Contract / MoU generator. Uses reportlab if present, else .txt fallback."""
from __future__ import annotations
import os
import time
import uuid
from typing import Any, Dict

OUTBOX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outbox")


def generate_mou(
    event: Dict[str, Any],
    brand: str,
    amount: float | None = None,
    terms: str | None = None,
) -> Dict[str, Any]:
    proposals = event.get("proposals", []) or []
    match = next((p for p in proposals if p.get("brand") == brand), None)
    if amount is None:
        amount = float(match.get("amount_inr", 25000)) if match else 25000.0
    deliverables = (match or {}).get("deliverables", ["Event branding + stall"]) or ["Event branding + stall"]

    mou_id = "mou_" + uuid.uuid4().hex[:8]
    mou = {
        "mou_id": mou_id,
        "brand": brand,
        "event": event.get("name", ""),
        "event_id": event.get("event_id", ""),
        "amount_inr": float(amount),
        "deliverables": deliverables,
        "terms": terms
        or (
            "Payment: 50% advance within 7 days of signing, 50% within 7 days post-event. "
            "Logo usage: sponsor logo on agreed collateral only. Cancellation: 14-day notice. "
            "Deliverables as listed; photo proof within 7 days post-event."
        ),
        "status": "draft",
        "created_at": time.time(),
    }

    pdf_path = None
    # try reportlab, fall back to .txt — never crash
    try:
        os.makedirs(OUTBOX_DIR, exist_ok=True)
        try:
            from reportlab.lib.pagesizes import A4  # type: ignore
            from reportlab.pdfgen import canvas  # type: ignore

            pdf_path = os.path.join(OUTBOX_DIR, f"{mou_id}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=A4)
            y = 800
            c.setFont("Helvetica-Bold", 16)
            c.drawString(60, y, "Memorandum of Understanding (MoU)")
            y -= 30
            c.setFont("Helvetica", 11)
            for line in [
                f"MoU ID: {mou_id}",
                f"Between: {event.get('name','Organizer')} (Organizer) and {brand} (Sponsor)",
                f"Event: {event.get('name')} | {event.get('location')} | {event.get('date')}",
                f"Amount: Rs {float(amount):,.0f}",
                "",
                "Deliverables:",
                *[f"  - {d}" for d in deliverables],
                "",
                "Terms:",
                f"  {mou['terms']}",
                "",
                "Sign: Organizer ______    Sponsor ______    Date ______",
            ]:
                for chunk in [line[i : i + 95] for i in range(0, max(len(line), 1), 95)]:
                    c.drawString(60, y, chunk)
                    y -= 15
                    if y < 60:
                        c.showPage()
                        y = 800
            c.save()
            mou["file"] = os.path.basename(pdf_path)
        except Exception:
            txt_path = os.path.join(OUTBOX_DIR, f"{mou_id}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(
                    f"MoU {mou_id}\n{event.get('name')} x {brand}\nAmount Rs {float(amount):,.0f}\n\n"
                    f"Deliverables:\n- " + "\n- ".join(deliverables) + f"\n\nTerms: {mou['terms']}\n"
                )
            mou["file"] = os.path.basename(txt_path)
            pdf_path = txt_path
    except Exception as e:  # noqa: BLE001
        mou["file_error"] = str(e)

    mou["pdf_path"] = pdf_path
    return mou
