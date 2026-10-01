"""Generate deterministic demo trace -> artifacts/trace_run1.jsonl.

Tries backend.graph.run_full_demo + gmail interrupt simulation if backend
exists; otherwise falls back to static deterministic payloads. No API keys
needed. Output: one JSON object per line with keys:
  {step, from_agent, to_agent, payload_summary, timestamp, llm_used, tool_used}
Covers: Loop A (A3->A2->A3 revise), contract trigger (A3->A4),
Loop B (A5 nudge), Loop C (A6->A1 feedback). >=14 steps.
"""
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BASE_TIME = datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc)

# (from_agent, to_agent, payload_summary, llm_used, tool_used)
STATIC_STEPS = [
    ("A1", "A2", "event brief TechFest2026 Pune 5000 footfall 18-24 tech passed; discovery query edtech/gaming within 15km", False, "maps"),
    ("A2", "A3", "ranked shortlist 6 brands with fit_score 0-100; top ByteLearn 87.5, GameKart 82.1, ChaiPoint 71.4", False, "scorer"),
    ("A3", "Brand", "outreach proposal PROP-TF2026-001 Gold Rs.45000 sent thread_demo_001 via gmail", True, "gmail"),
    ("Brand", "A3", "reply: 'love it but half budget, can you reduce price?' classified pushback", False, "gmail"),
    ("A3", "A2", "Loop A revise request: budget constraint Rs.25000-32000, rescore lower tier", False, "gmail"),
    ("A2", "A3", "Loop A rescore: Silver+workshop tier fit 84.2 revised price Rs.32000", False, "scorer"),
    ("A3", "Brand", "revised proposal Rs.32000 sent (price reduced 28.9%) via gmail", True, "gmail"),
    ("Brand", "A3", "reply: 'yes agreed, let's sign the MoU' classified yes", False, "gmail"),
    ("A3", "A4", "contract trigger: yes -> draft MoU PROP-TF2026-001 Rs.32000 deliverables x4", True, None),
    ("A4", "Brand", "MoU sent v1 payment 50/50 validity 14d via gmail", True, "gmail"),
    ("A5", "Brand", "Loop B nudge: follow-up check-in 48h no-response timer + payment reminder", True, "gmail"),
    ("A6", "Event", "audit deliverables 4/4 stage_banner stall logo reel; count_logos poster=3 stall=2 compliance 100%", False, "vision"),
    ("A6", "A1", "Loop C feedback: learning_update weights distance 0.30->0.22 category 0.50->0.56", False, None),
    ("A1", "System", "ROI report 3.66x (Rs.32000 -> Rs.117000) demo complete", True, None),
]


def _try_backend():
    info = {}
    # 1) try new graph (may be broken due to state imports — catch all)
    try:
        graph = importlib.import_module("backend.graph")
    except Exception as e:  # noqa: BLE001
        graph = None
        info["graph_import_error"] = str(e)[:200]
    if graph is not None and hasattr(graph, "run_full_demo"):
        try:
            demo = graph.run_full_demo()

            # summarize counts deterministically
            def _len(x):
                try:
                    return len(x)
                except Exception:
                    return 0
            def _get(o, *ks):
                for k in ks:
                    if isinstance(o, dict) and k in o:
                        return o[k]
                    if hasattr(o, k):
                        return getattr(o, k)
                return None
            brands = _get(demo, "brands", "shortlist", "ranked_brands")
            proposals = _get(demo, "proposals", "outreach", "emails")
            info["demo_brands"] = _len(brands)
            info["demo_proposals"] = _len(proposals)
        except Exception as e:  # noqa: BLE001
            info["demo_error"] = str(e)[:200]
    # 2) fallback dict-flow demo (working offline agents) for live counts
    if "demo_brands" not in info:
        try:
            disc = importlib.import_module("backend.agents.discovery")
            prop = importlib.import_module("backend.agents.proposal")
            evt = {"name": "TechFest 2026", "location": "Pune",
                   "footfall": 5000, "audience": "tech students 18-24"}
            brands = disc.discover(evt, top_k=8)
            evt["discovery"] = brands
            proposals = prop.propose(evt)
            info["demo_brands"] = len(brands)
            info["demo_proposals"] = len(proposals)
            # gmail interrupt simulation (real classify + revise)
            gmail = importlib.import_module("backend.tools.gmail")
            info["interrupt_pushback"] = gmail.classify_reply("love it but half budget")
            info["interrupt_yes"] = gmail.classify_reply("yes agreed")
            rev = prop.revise_proposal(proposals[0], "love it but half budget")
            info["revised_price"] = rev.get("amount_inr")
        except Exception as e:  # noqa: BLE001
            info["dict_flow_error"] = str(e)[:200]
    # 3) gmail handler on graph if present
    if graph is not None:
        handler = None
        for n in ("handle_gmail_reply", "gmail_interrupt", "on_reply", "route_reply", "handle_reply"):
            if hasattr(graph, n):
                handler = getattr(graph, n)
                break
        if handler is not None:
            for label, text in (("pushback", "love it but half budget"), ("yes", "yes agreed")):
                try:
                    try:
                        out = handler(text, {"price": 45000})
                    except TypeError:
                        out = handler({"reply": text, "price": 45000})
                    info[f"interrupt_{label}"] = str(out)[:200]
                except Exception as e:  # noqa: BLE001
                    info[f"interrupt_{label}_error"] = str(e)[:200]
    return info


def main():
    backend_info = _try_backend()
    out_path = Path(__file__).resolve().parents[1] / "artifacts" / "trace_run1.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, (frm, to, summary, llm, tool) in enumerate(STATIC_STEPS, start=1):
        if i == 2 and "demo_brands" in backend_info:
            summary += f" [live demo brands={backend_info['demo_brands']} proposals={backend_info.get('demo_proposals')}]"
        if i == 5 and "interrupt_pushback" in backend_info:
            summary += f" [live {backend_info['interrupt_pushback']}]"
        if i == 9 and "interrupt_yes" in backend_info:
            summary += f" [live {backend_info['interrupt_yes']}]"
        ts = (BASE_TIME + timedelta(seconds=i * 5)).isoformat()
        rec = {
            "step": i,
            "from_agent": frm,
            "to_agent": to,
            "payload_summary": summary,
            "timestamp": ts,
            "llm_used": llm,
            "tool_used": tool,
        }
        lines.append(rec)
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in lines:
            f.write(json.dumps(rec) + "\n")
    print(f"wrote {len(lines)} steps -> {out_path} backend_info={backend_info}")


if __name__ == "__main__":
    main()
