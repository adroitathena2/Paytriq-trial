"""Shared state for Paytriq trial: dict store (FastAPI) + Pydantic models (graph demo). Offline, no DB."""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

STORE: Dict[str, Dict[str, Any]] = {}
LEARNING: Dict[str, Any] = {
    "runs": 0,
    "avg_roi": 0.0,
    "brand_feedback": {},
    "history": [],
}


def new_event_id() -> str:
    return "evt_" + uuid.uuid4().hex[:8]


def create_event(data: Dict[str, Any]) -> Dict[str, Any]:
    eid = new_event_id()
    now = time.time()
    event = {
        "event_id": eid,
        "name": data.get("name", "Untitled Event"),
        "location": data.get("location", ""),
        "footfall": int(data.get("footfall", 0) or 0),
        "date": data.get("date", ""),
        "audience": data.get("audience", "students"),
        "budget": data.get("budget", None),
        "status": "created",
        "created_at": now,
        "discovery": [],
        "proposals": [],
        "outreach": [],
        "replies": [],
        "mous": [],
        "compliance": [],
        "roi": None,
        "errors": [],
    }
    STORE[eid] = event
    return event


def get_event(event_id: str) -> Dict[str, Any] | None:
    return STORE.get(event_id)


def update_event(event_id: str, patch: Dict[str, Any]) -> Dict[str, Any] | None:
    evt = STORE.get(event_id)
    if not evt:
        return None
    evt.update(patch)
    return evt


def list_events() -> List[Dict[str, Any]]:
    return list(STORE.values())


def record_learning(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Update global LEARNING with one ROI run. Never raises."""
    try:
        LEARNING["runs"] += 1
        roi = float(entry.get("roi", 0) or 0)
        n = LEARNING["runs"]
        prev = float(LEARNING.get("avg_roi", 0) or 0)
        LEARNING["avg_roi"] = round(((prev * (n - 1)) + roi) / n, 3)
        LEARNING["history"].append(entry)
        for b, f in (entry.get("brand_feedback") or {}).items():
            LEARNING["brand_feedback"][b] = f
    except Exception as e:  # noqa: BLE001 - learning must never crash
        LEARNING.setdefault("errors", []).append(str(e))
    return LEARNING


# ---------------------------------------------------------------------------
# Typed agent schema (A1-A6 graph). Coexists with the dict STORE above, which
# the FastAPI layer (/api/*) uses. These dataclasses are consumed by
# backend.agents.a1_* .. a6_* and backend.graph.PaytriqGraph. Offline.
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field as _field


@dataclass
class EventProfile:
    name: str = "TechFest Pune"
    location: str = "Pune"
    footfall: int = 5000
    audience: str = "tech students"
    date: str = "2026-11-15"
    budget: float | None = None


@dataclass
class BrandLead:
    name: str = ""
    category: str = ""
    distance_km: float = 0.0
    phone: str = ""
    rating: float = 4.0
    fit_score: float = 0.0
    why_fit: str = ""
    icebreaker: str = ""


@dataclass
class Proposal:
    brand: str = ""
    tier: str = ""
    amount: int = 0
    deliverables: list = _field(default_factory=list)
    cover_letter: str = ""


@dataclass
class OutreachThread:
    brand: str = ""
    email: str = ""
    day: int = 0
    status: str = "draft"
    reply_text: str = ""
    intent: str = ""


@dataclass
class Deliverable:
    promise: str = ""


@dataclass
class EventState:
    event: EventProfile = _field(default_factory=EventProfile)
    brands: list = _field(default_factory=list)
    proposals: list = _field(default_factory=list)
    threads: list = _field(default_factory=list)
    deliverables: list = _field(default_factory=list)
    roi_report: dict = _field(default_factory=dict)
    negotiation_status: str = "init"
    compliance_score: float = 0.0

    # alias properties so dict-or-object consumers (tests, trace, CLI) work
    @property
    def shortlist(self):  # pragma: no cover - alias
        return self.brands

    @property
    def ranked_brands(self):  # pragma: no cover - alias
        return self.brands

    @property
    def outreach(self):  # pragma: no cover - alias
        return self.proposals

    @property
    def emails(self):  # pragma: no cover - alias
        return self.proposals

    @property
    def gmail_threads(self):  # pragma: no cover - alias
        return self.threads

    @property
    def conversations(self):  # pragma: no cover - alias
        return self.threads

    @property
    def mou(self):  # pragma: no cover - alias
        return (self.roi_report or {}).get("mou")

    @property
    def contract(self):  # pragma: no cover - alias
        return (self.roi_report or {}).get("mou")

    @property
    def mous(self):  # pragma: no cover - alias
        m = (self.roi_report or {}).get("mou")
        return [m] if m else []

    @property
    def roi(self):  # pragma: no cover - alias
        return self.roi_report

    @property
    def roi_summary(self):  # pragma: no cover - alias
        return self.roi_report


def new_event_state(**kwargs: Any) -> EventState:
    """Build an EventState from loose demo kwargs (tolerant key names)."""
    name = kwargs.get("name", kwargs.get("event_name", "TechFest Pune"))
    location = kwargs.get("location", "Pune")
    try:
        footfall = int(kwargs.get("footfall", 5000) or 5000)
    except (TypeError, ValueError):
        footfall = 5000
    audience = kwargs.get("audience", "tech students")
    if not isinstance(audience, str):
        interests = kwargs.get("audience_interests") or kwargs.get("audience_age") or audience
        audience = ", ".join(interests) if isinstance(interests, list) else str(interests or "tech students")
    date = str(kwargs.get("date", "2026-11-15"))
    budget = kwargs.get("budget", kwargs.get("budget_range"))
    if isinstance(budget, (list, tuple)) and budget:
        try:
            budget = float(budget[-1])
        except (TypeError, ValueError):
            budget = None
    return EventState(
        event=EventProfile(
            name=str(name), location=str(location), footfall=footfall,
            audience=str(audience), date=date, budget=budget,
        )
    )


# ---------- Pydantic models for graph demo (A1-A6) ----------
class EventProfile(BaseModel):
    """College fest / event profile."""
    name: str = "TechFest 2026"
    dates: str = "2026-11-10 to 2026-11-12"
    footfall: int = 5000
    audience: str = "college students 18-24"
    location: str = "Pune, Maharashtra"
    contact_email: str = "organizer@college.edu"


class BrandLead(BaseModel):
    """A local brand candidate."""
    name: str
    category: str
    distance_km: float = 0.0
    phone: str = ""
    rating: float = 0.0
    fit_score: float = 0.0
    why_fit: str = ""
    icebreaker: str = ""


class Proposal(BaseModel):
    """Sponsorship proposal for one brand."""
    brand: str
    tier: str = "Co-Sponsor"
    amount: int = 15000
    deliverables: List[str] = Field(default_factory=list)
    cover_letter: str = ""
    pdf_path: str = ""


class OutreachThread(BaseModel):
    """One email thread with a brand."""
    brand: str
    email: str = ""
    day: int = 0
    status: str = "pending"
    reply_text: str = ""
    intent: str = "none"


class Deliverable(BaseModel):
    """Promised deliverable + fulfilment status."""
    promise: str
    status: str = "pending"
    evidence: str = ""


class EventState(BaseModel):
    """Supervisor state passed between agents."""
    event: EventProfile = Field(default_factory=EventProfile)
    brands: List[BrandLead] = Field(default_factory=list)
    proposals: List[Proposal] = Field(default_factory=list)
    threads: List[OutreachThread] = Field(default_factory=list)
    deliverables: List[Deliverable] = Field(default_factory=list)
    negotiation_status: str = "discovery"
    compliance_score: float = 0.0
    roi_report: Dict[str, Any] = Field(default_factory=dict)

    @property
    def mou(self) -> Optional[Any]:
        """Compat alias: MoU lives inside roi_report after A4."""
        return self.roi_report.get("mou")

    @property
    def roi(self) -> Dict[str, Any]:
        """Compat alias for tests looking for .roi."""
        return self.roi_report


def new_event_state(**kwargs) -> EventState:
    """Build a fresh EventState with optional EventProfile overrides."""
    event_kwargs = {k: v for k, v in kwargs.items() if k in EventProfile.model_fields}
    state_kwargs = {k: v for k, v in kwargs.items() if k not in EventProfile.model_fields}
    event = EventProfile(**event_kwargs) if event_kwargs else EventProfile()
    return EventState(event=event, **state_kwargs)
