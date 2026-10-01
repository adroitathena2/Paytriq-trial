"""Paytriq FastAPI backend. Run with: uvicorn backend.main:app (from Paytriq-trial/). Offline, no keys."""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.state import STORE, LEARNING, create_event, get_event, list_events, record_learning

app = FastAPI(title="Paytriq API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic request models ----------
class CreateEventRequest(BaseModel):
    name: str = Field(default="TechFest Pune")
    location: str = Field(default="Pune")
    footfall: int = Field(default=5000)
    date: str = Field(default="2026-11-15")
    audience: str = Field(default="tech students")
    budget: Optional[float] = None


class ProposeRequest(BaseModel):
    event_id: str
    brands: Optional[List[str]] = None


class OutreachSendRequest(BaseModel):
    event_id: str
    approve: bool = False
    brands: Optional[List[str]] = None


class GmailWebhookRequest(BaseModel):
    event_id: str
    from_brand: str = "Unknown"
    subject: str = ""
    body: str = ""


class MouRequest(BaseModel):
    event_id: str
    brand: str
    amount: Optional[float] = None
    terms: Optional[str] = None


class ComplianceCheckRequest(BaseModel):
    event_id: str
    brand: Optional[str] = None


class RoiRequest(BaseModel):
    event_id: str
    actual_spend: Optional[float] = None
    actual_leads: Optional[int] = None


def _err(event, msg: str):
    try:
        event.setdefault("errors", []).append(msg)
    except Exception:
        pass


# ---------- routes ----------
@app.get("/")
def root():
    return {"service": "Paytriq API", "version": "0.1.0", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok", "events": len(STORE)}


@app.get("/api/state")
def api_state(event_id: Optional[str] = None):
    if event_id:
        evt = get_event(event_id)
        if not evt:
            return {"error": f"unknown event_id {event_id}"}
        return {"event": evt, "learning": LEARNING}
    return {"events": list_events(), "learning": LEARNING}


@app.post("/api/event")
def api_create_event(req: CreateEventRequest):
    try:
        evt = create_event(req.model_dump())
    except Exception as e:  # noqa: BLE001 - never 500
        return {"error": f"create_event failed: {e}", "event": None}
    # A1 discovery with graceful fallback
    try:
        from backend.agents.discovery import discover

        evt["discovery"] = discover(evt)
        evt["status"] = "discovered"
    except Exception as e:  # noqa: BLE001
        evt["discovery"] = []
        _err(evt, f"A1 discovery failed: {e}")
        return {"event": evt, "discovery": [], "error": f"A1 discovery failed: {e}"}
    return {"event": evt, "discovery": evt["discovery"]}


@app.post("/api/propose")
def api_propose(req: ProposeRequest):
    evt = get_event(req.event_id)
    if not evt:
        return {"error": f"unknown event_id {req.event_id}"}
    try:
        from backend.agents.proposal import propose

        proposals = propose(evt, req.brands)
        evt["proposals"] = proposals
        evt["status"] = "proposed"
        return {"event_id": req.event_id, "proposals": proposals}
    except Exception as e:  # noqa: BLE001
        _err(evt, f"A2 propose failed: {e}")
        return {"event_id": req.event_id, "proposals": evt.get("proposals", []), "error": f"A2 failed: {e}"}


@app.post("/api/outreach/send")
def api_outreach_send(req: OutreachSendRequest):
    evt = get_event(req.event_id)
    if not evt:
        return {"error": f"unknown event_id {req.event_id}"}
    # HUMAN GATE: explicit approve=true required
    if req.approve is not True:
        return {
            "event_id": req.event_id,
            "sent": [],
            "count": 0,
            "gated": True,
            "error": "Human approval required: pass approve=true to send. Nothing was sent.",
        }
    try:
        from backend.agents.outreach import send_outreach

        result = send_outreach(evt, req.brands)
        evt["outreach"].extend(result.get("sent", []))
        if result.get("errors"):
            for m in result["errors"]:
                _err(evt, f"A3: {m}")
        evt["status"] = "outreach_sent"
        out = {"event_id": req.event_id, **result}
        if result.get("errors"):
            out["error"] = "; ".join(result["errors"])
        return out
    except Exception as e:  # noqa: BLE001
        _err(evt, f"A3 outreach failed: {e}")
        return {"event_id": req.event_id, "sent": [], "count": 0, "error": f"A3 failed: {e}"}


PUSHBACK_KEYWORDS = ["too high", "expensive", "discount", "negotiat", "budget", "reduce", "lower", "price"]
YES_KEYWORDS = ["yes", "interested", "agree", "approved", "confirm", "let's proceed", "lets proceed", "deal", "sign"]


@app.post("/api/gmail/webhook")
def api_gmail_webhook(req: GmailWebhookRequest):
    """Incoming reply -> conditional route to A2 revise (pushback) or A4 MoU (yes)."""
    evt = get_event(req.event_id)
    if not evt:
        return {"error": f"unknown event_id {req.event_id}"}
    body = (req.body or "").lower()
    evt["replies"].append({"from_brand": req.from_brand, "subject": req.subject, "body": req.body})

    is_pushback = any(k in body for k in PUSHBACK_KEYWORDS)
    is_yes = any(k in body for k in YES_KEYWORDS)

    if is_pushback:
        try:
            from backend.agents.proposal import revise_proposal

            proposals = evt.get("proposals", []) or []
            target = next((p for p in proposals if p.get("brand") == req.from_brand), proposals[0] if proposals else None)
            if not target:
                return {"route": "A2_revise", "error": "no proposal to revise — run /api/propose first"}
            revised = revise_proposal(target, req.body)
            # replace in list
            for i, p in enumerate(proposals):
                if p.get("brand") == revised.get("brand"):
                    proposals[i] = revised
                    break
            evt["proposals"] = proposals
            return {"route": "A2_revise", "brand": req.from_brand, "revised": revised}
        except Exception as e:  # noqa: BLE001
            _err(evt, f"webhook A2 revise failed: {e}")
            return {"route": "A2_revise", "error": f"revise failed: {e}"}

    if is_yes:
        try:
            from backend.agents.contract import generate_mou

            mou = generate_mou(evt, req.from_brand)
            evt["mous"].append(mou)
            evt["status"] = "mou_draft"
            return {"route": "A4_mou", "brand": req.from_brand, "mou": mou}
        except Exception as e:  # noqa: BLE001
            _err(evt, f"webhook A4 mou failed: {e}")
            return {"route": "A4_mou", "error": f"mou failed: {e}"}

    return {
        "route": "human_review",
        "brand": req.from_brand,
        "note": "Reply did not match pushback/yes keywords — queued for human review. No agent action taken.",
    }


@app.post("/api/contract/mou")
def api_mou(req: MouRequest):
    evt = get_event(req.event_id)
    if not evt:
        return {"error": f"unknown event_id {req.event_id}"}
    try:
        from backend.agents.contract import generate_mou

        mou = generate_mou(evt, req.brand, req.amount, req.terms)
        evt["mous"].append(mou)
        evt["status"] = "mou_draft"
        return {"event_id": req.event_id, "mou": mou}
    except Exception as e:  # noqa: BLE001
        _err(evt, f"A4 mou failed: {e}")
        return {"event_id": req.event_id, "mou": None, "error": f"A4 failed: {e}"}


@app.post("/api/compliance/check")
def api_compliance(req: ComplianceCheckRequest):
    evt = get_event(req.event_id)
    if not evt:
        return {"error": f"unknown event_id {req.event_id}"}
    try:
        from backend.agents.compliance import check_compliance

        mou = None
        if req.brand:
            mous = evt.get("mous", []) or []
            mou = next((m for m in mous if m.get("brand") == req.brand), None)
        result = check_compliance(evt, mou)
        evt["compliance"].append(result)
        return {"event_id": req.event_id, **result}
    except Exception as e:  # noqa: BLE001
        _err(evt, f"A5 compliance failed: {e}")
        return {"event_id": req.event_id, "passed": False, "score": 0, "issues": [str(e)], "error": f"A5 failed: {e}"}


@app.post("/api/audit/roi")
def api_roi(req: RoiRequest):
    evt = get_event(req.event_id)
    if not evt:
        return {"error": f"unknown event_id {req.event_id}"}
    try:
        from backend.agents.audit import compute_roi

        roi = compute_roi(evt, req.actual_spend, req.actual_leads)
        evt["roi"] = roi
        evt["status"] = "audited"
        learning = record_learning(
            {
                "event_id": req.event_id,
                "roi": roi.get("roi"),
                "brand_feedback": {m.get("brand"): "signed" for m in (evt.get("mous") or [])},
            }
        )
        return {"event_id": req.event_id, "roi": roi, "learning": learning}
    except Exception as e:  # noqa: BLE001
        _err(evt, f"A6 roi failed: {e}")
        return {"event_id": req.event_id, "roi": None, "error": f"A6 failed: {e}"}
