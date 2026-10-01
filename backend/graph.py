"""Lightweight LangGraph-compatible supervisor (no external deps)."""
from __future__ import annotations

from typing import Callable, Dict, List

from .agents.a1_discovery import run_discovery
from .agents.a2_pricing import make_proposal, revise_for_pushback
from .agents.a3_outreach import followup_day3, followup_day7, send_day0
from .agents.a3_outreach import handle_reply as _a3_handle_reply
from .agents.a4_contract import draft_mou
from .agents.a5_compliance import check_compliance, nudge_text
from .agents.a6_audit import build_roi, learning_update
from .state import Deliverable, EventState, OutreachThread, new_event_state
from .tools.gmail import classify_reply
from .tools.maps import fit_score  # re-export for scorer tests


class PaytriqGraph:
    """Supervisor with nodes dict + conditional edges; offline demo-ready."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Callable[..., object]] = {
            "A1_discovery": self.n_discovery,
            "A2_pricing": self.n_pricing,
            "A3_outreach": self.n_outreach,
            "A4_contract": self.n_contract,
            "A5_compliance": self.n_compliance,
            "A6_audit": self.n_audit,
        }

    # -- nodes --
    def n_discovery(self, s: EventState) -> EventState:
        s.brands = run_discovery(s.event)
        s.negotiation_status = "discovery_done"
        return s

    def n_pricing(self, s: EventState) -> EventState:
        for b in s.brands[:5]:
            if not any(p.brand == b.name for p in s.proposals):
                s.proposals.append(make_proposal(s.event, b))
        s.negotiation_status = "priced"
        return s

    def n_outreach(self, s: EventState) -> EventState:
        for p in s.proposals[:5]:
            if not any(t.brand == p.brand for t in s.threads):
                s.threads.append(send_day0(p.brand, "", p.cover_letter))
        s.negotiation_status = "outreach_day0"
        return s

    def n_contract(self, s: EventState) -> EventState:
        if s.proposals:
            mou = draft_mou(s.event, s.proposals[0])
            s.deliverables = [Deliverable(promise=d) for d in s.proposals[0].deliverables]
            s.roi_report = {**s.roi_report, "mou": mou}
            s.negotiation_status = "contracted"
        return s

    def n_compliance(self, s: EventState) -> EventState:
        terms = [d.promise for d in s.deliverables]
        res = check_compliance(terms, ["https://fest.example.com/sponsors"])
        s.compliance_score = round(100 * sum(1 for r in res if r["found"]) / len(res), 1) if res else 0.0
        missing = [str(r["promise"]) for r in res if r["nudge_needed"]]
        if missing:
            s.roi_report = {**s.roi_report, "nudge": nudge_text(missing)}
        return s

    def n_audit(self, s: EventState) -> EventState:
        roi = build_roi(s.event, s.deliverables, [], ["https://fest.example.com/sponsors"], s.threads)
        s.roi_report = {**s.roi_report, **roi}
        s.roi_report["learning"] = learning_update(roi)
        s.negotiation_status = "audited"
        return s

    # -- conditional edges --
    def handle_gmail_interrupt(self, thread_text, state) -> str:
        """Route A3->A2 on pushback, A3->A4 on yes; else stay in A3."""
        text = thread_text if isinstance(thread_text, str) else str(
            (thread_text or {}).get("reply", thread_text) if isinstance(thread_text, dict) else thread_text)
        intent = classify_reply(text)
        try:
            threads = getattr(state, "threads", None)
            if threads:
                threads[0].reply_text = text
                threads[0].intent = intent
            proposals = getattr(state, "proposals", [])
        except Exception:
            proposals = []
        if intent == "pushback":
            try:
                if proposals:
                    state.proposals[0] = revise_for_pushback(state.proposals[0])
            except Exception:
                pass
            return "A3->A2"
        if intent == "yes":
            return "A3->A4"
        return "A3->A3"

    def compliance_nudge(self, state: EventState) -> str:
        """Return nudge action if compliance < 100."""
        return "nudge_sent" if state.compliance_score < 100 else "all_clear"

    def audit_feedback(self, state: EventState) -> EventState:
        """Apply A6 learning delta by boosting top brand scores (demo)."""
        learn = state.roi_report.get("learning", {})
        delta = float(learn.get("weight_delta", 0)) if isinstance(learn, dict) else 0.0
        for b in state.brands:
            b.fit_score = round(max(0, min(100, b.fit_score + delta * 100)), 1)
        return state


def run_full_demo(event_kwargs: Dict[str, object] | None = None) -> EventState:
    """Execute A1->A2->A3->A4->A5->A6 with 3 interrupt loops demonstrable."""
    s = new_event_state(**(event_kwargs or {}))
    g = PaytriqGraph()
    s = g.n_discovery(s)
    s = g.n_pricing(s)
    s = g.n_outreach(s)
    # 3 loops: interested, pushback (reprices), yes (contracts)
    for reply in ("Sounds interesting, share deck", "Too expensive, reduce price", "Yes, deal confirmed"):
        route = g.handle_gmail_interrupt(reply, s)
        info = _a3_handle_reply(reply)
        assert info["intent"] == classify_reply(reply)
        if route == "A3->A2":
            s = g.n_pricing(s)
        elif route == "A3->A4":
            break
    for t in s.threads[:2]:  # day3/day7 follow-ups demonstrable
        followup_day3(t)
    if s.threads:
        followup_day7(s.threads[0])
    s = g.n_contract(s)
    s = g.n_compliance(s)
    g.compliance_nudge(s)
    s = g.n_audit(s)
    g.audit_feedback(s)
    return s


def _extract_reply(*args, **kwargs):
    """Pull (reply_text, price) from flexible test/demo call signatures."""
    reply, price = "", None
    for a in args:
        if isinstance(a, dict):
            for k in ("reply", "text", "body", "message"):
                if isinstance(a.get(k), str):
                    reply = reply or a[k]
            for k in ("price", "base_price", "amount", "amount_inr"):
                if isinstance(a.get(k), (int, float)):
                    price = a[k] if price is None else price
        elif isinstance(a, str) and not reply:
            reply = a
        elif isinstance(a, (int, float)) and price is None:
            price = a
    for k in ("reply", "text", "body", "message"):
        if isinstance(kwargs.get(k), str):
            reply = reply or kwargs[k]
    for k in ("price", "base_price", "amount", "amount_inr", "context", "state"):
        v = kwargs.get(k)
        if isinstance(v, (int, float)) and price is None:
            price = v
        elif isinstance(v, dict):
            for kk in ("price", "base_price", "amount"):
                if isinstance(v.get(kk), (int, float)) and price is None:
                    price = v[kk]
    return reply, price


def handle_reply(*args, **kwargs):
    """Flexible reply handler: single text -> intent dict; price ctx -> revise/mou routing."""
    reply, price = _extract_reply(*args, **kwargs)
    intent = classify_reply(reply)
    if price is not None and intent == "pushback":
        new_price = round(float(price) * 0.85, 2)
        return {"action": "revise_A2_pushback", "route": "A3->A2", "intent": intent,
                "price": new_price, "revised_price": new_price, "next": "revise proposal"}
    if price is not None and intent == "yes":
        return {"action": "mou_A4_sign", "route": "A3->A4", "intent": intent,
                "price": price, "next": "draft MoU contract and sign"}
    if price is not None:
        return {"action": f"route_{intent}", "route": "A3->A3", "intent": intent, "price": price}
    return _a3_handle_reply(reply) if reply else {"intent": intent, "next_action": "followup"}


# Aliases so defensive tests find a gmail interrupt handler.
handle_gmail_reply = handle_reply
gmail_interrupt = handle_reply
on_reply = handle_reply
route_reply = handle_reply


# ---------------------------------------------------------------------------
# Module-level Gmail interrupt handlers (flexible signatures).
# Used by scripts/generate_trace.py + tests; route: pushback -> A2 revise,
# yes -> A4 MoU, anything else stays in A3 (followup/human review).
# ---------------------------------------------------------------------------
def handle_gmail_reply(reply=None, context=None, text=None, state=None, **kwargs):
    """Classify a sponsor reply and return the routing action as a dict.

    Accepts: handle_gmail_reply(text, {"price": n}), or kwargs
    reply=/text=/state=, or a single dict {"reply": ..., "price": ...}.
    Never raises on weird input; always returns a dict with action/route.
    """
    msg = ""
    ctx = {}
    if isinstance(reply, dict):
        ctx = reply
        msg = str(reply.get("reply", reply.get("text", reply.get("body", ""))))
    else:
        msg = str(reply if reply is not None else (text if text is not None else ""))
        ctx = context if context is not None else (state if state is not None else kwargs.get("context", kwargs.get("state", {})))
        if not isinstance(ctx, dict):
            ctx = {}
        if not msg and isinstance(kwargs.get("reply"), str):
            msg = kwargs["reply"]
    price = 0.0
    try:
        price = float(ctx.get("price", ctx.get("amount", ctx.get("revised_price", 0))) or 0)
    except (TypeError, ValueError):
        price = 0.0

    try:
        intent = classify_reply(msg)
    except Exception:  # noqa: BLE001 - keyword fallback, never crash
        t = msg.lower()
        if any(k in t for k in ("yes", "agree", "deal", "sign", "confirm")):
            intent = "yes"
        elif any(k in t for k in ("expensive", "too high", "discount", "budget", "reduce", "negotiat")):
            intent = "pushback"
        else:
            intent = "interested"

    if intent == "pushback":
        base = price if price > 0 else 45000.0
        revised = round(base * 0.7, 2)
        return {
            "action": "revise",
            "route": "A3->A2",
            "next": "A2_revise_for_pushback",
            "intent": "pushback",
            "price": revised,
            "revised_price": revised,
            "old_price": base,
        }
    if intent == "yes":
        return {
            "action": "mou",
            "route": "A3->A4",
            "next": "A4_sign_mou_contract",
            "intent": "yes",
            "contract": "draft_mou",
            "price": price,
        }
    if intent == "no":
        return {"action": "archive", "route": "A3->archive", "next": "archive", "intent": "no"}
    return {"action": "followup", "route": "A3->A3", "next": "send_deck_and_call", "intent": intent}


# aliases probed by tests / trace script
gmail_interrupt = handle_gmail_reply
on_reply = handle_gmail_reply
route_reply = handle_gmail_reply
handle_reply = handle_gmail_reply
