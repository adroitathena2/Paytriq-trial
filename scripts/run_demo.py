"""CLI demo for evaluators without UI. Prints each agent step.

Tolerant: works whether backend.graph.run_full_demo returns a steps dict
(API-style demo) or an EventState object (graph-style demo). Offline, no keys.
"""
from __future__ import annotations
import json
import sys

sys.path.insert(0, ".")

from backend.graph import run_full_demo


def _get(o, *keys):
    for k in keys:
        if isinstance(o, dict) and k in o:
            return o[k]
        if hasattr(o, k):
            return getattr(o, k)
    return None


def _brand_name(b):
    return b.get("brand", b.get("name")) if isinstance(b, dict) else getattr(b, "brand", getattr(b, "name", b))


def main() -> None:
    steps = run_full_demo()
    print("=== Paytriq full demo (offline) ===")
    if isinstance(steps, dict):
        print(f"event_id: {steps.get('event_id')}")
        print(f"\n[1] A1 discovery ({len(steps.get('A1_discovery', []))} brands):")
        for d in (steps.get("A1_discovery", []) or [])[:5]:
            print(f"  - {d['brand']} ({d['category']}) fit={d['fit_score']} :: {str(d['reason'])[:80]}")
        print("\n[2] A2 proposals:")
        for p in steps.get("A2_proposals", []) or []:
            print(f"  - {p['brand']}: {p['tier']} Rs {p['amount_inr']:,.0f}")
        a3 = steps.get("A3_outreach", {}) or {}
        print("\n[3] A3 outreach:", json.dumps({k: v for k, v in a3.items() if k != "sent"})[:300])
        print("    sent:", [s.get("brand") for s in a3.get("sent", [])])
        rev = steps.get("A2_revise_after_pushback", {}) or {}
        print(f"\n[4] A2 revise (pushback): {rev.get('brand')} Rs {rev.get('amount_inr')} :: {rev.get('revision_note')}")
        mou = steps.get("A4_mou", {}) or {}
        print(f"\n[5] A4 MoU: {mou.get('mou_id')} {mou.get('brand')} Rs {mou.get('amount_inr')} file={mou.get('file')}")
        print("\n[6] A5 compliance:", json.dumps(steps.get("A5_compliance", {}))[:300])
        print("\n[7] A6 ROI:", json.dumps(steps.get("A6_roi", {}))[:300])
        print("\n[8] learning:", json.dumps(steps.get("learning", {}))[:300])
    else:
        # EventState-style object from backend.graph
        brands = _get(steps, "brands", "shortlist", "ranked_brands") or []
        proposals = _get(steps, "proposals", "outreach", "emails") or []
        threads = _get(steps, "threads", "gmail_threads", "conversations") or []
        roi = _get(steps, "roi", "roi_report", "roi_summary") or {}
        print(f"status: {getattr(steps, 'negotiation_status', '?')}")
        print(f"\n[1] A1 discovery ({len(brands)} brands):")
        for b in list(brands)[:5]:
            nm = _brand_name(b)
            fit = b.get("fit_score") if isinstance(b, dict) else getattr(b, "fit_score", "?")
            print(f"  - {nm} fit={fit}")
        print("\n[2] A2 proposals:")
        for p in list(proposals):
            if isinstance(p, dict):
                print(f"  - {p.get('brand')}: {p.get('tier')} Rs {p.get('amount', 0):,.0f}")
            else:
                print(f"  - {p.brand}: {p.tier} Rs {p.amount:,.0f}")
        print(f"\n[3] A3 outreach threads: {len(threads)}")
        print("\n[4] A4 MoU:", json.dumps(_get(steps, "mou", "contract") or {}, default=str)[:300])
        print(f"\n[5] A5 compliance_score: {getattr(steps, 'compliance_score', '?')}")
        print("\n[6] A6 ROI:", json.dumps(roi, default=str)[:400])
    print("\nDone.")


if __name__ == "__main__":
    main()
