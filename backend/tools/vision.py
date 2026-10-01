"""Vision + audit helpers (deterministic mocks, offline-safe)."""
from __future__ import annotations

import hashlib
from typing import Dict, List


def count_logos(image_path_or_url=None, *extra) -> Dict[str, object]:
    """Mock logo/footfall counter — deterministic, offline-safe.

    Accepts a path/url string, a list of detections, or a dict.
    Lists of detections return per-brand counts; strings return mock estimates.
    """
    if extra and image_path_or_url is None:
        image_path_or_url = extra[0]
    inp = image_path_or_url
    if isinstance(inp, dict):
        dets = inp.get("detections", inp.get("labels", []))
        if isinstance(dets, list):
            inp = dets
        else:
            return {"mock": 1, "footfall_estimate": 800}
    if isinstance(inp, (list, tuple)):
        counts: Dict[str, object] = {}
        for d in inp:
            label = d.get("label", d) if isinstance(d, dict) else d
            label = str(label)
            counts[label] = int(counts.get(label, 0)) + 1  # type: ignore
        if not counts:
            counts = {"mock": 1}
        return counts
    h = int(hashlib.md5(str(inp).encode()).hexdigest()[:4], 16)
    logo_count = (h % 5) + 1
    footfall_estimate = 500 + (h % 40) * 100
    return {
        "logo_count": logo_count,
        "footfall_estimate": footfall_estimate,
        "notes": f"mock vision on {inp}: {logo_count} logos visible",
    }


def audit_deliverables(promises=None, photos=None, links=None, **kwargs) -> Dict[str, object]:
    """Score compliance % — supports (promises, evidence_dict) or (promises, photos, links)."""
    if promises is None:
        promises = kwargs.get("promised", kwargs.get("deliverables", []))
    if isinstance(promises, dict):  # called as fn({"promised":..,"evidence":..})
        photos = promises.get("evidence", [])
        promises = promises.get("promised", promises.get("deliverables", []))
    evidence = kwargs.get("evidence", None)
    if isinstance(photos, dict) or isinstance(evidence, dict):
        ev = photos if isinstance(photos, dict) else evidence
        assert isinstance(ev, dict)
        done = sum(1 for p in (promises or []) if bool(ev.get(p)))
        total = len(promises or [])
        pct = round(100.0 * done / total, 1) if total else 0.0
        findings = [{"promise": p, "found": bool(ev.get(p))} for p in (promises or [])]
        return {"compliance_pct": pct, "compliance": pct, "score": pct,
                "fulfilled": done, "total": total, "findings": findings}
    pics = list(photos or [])
    urls = list(links or [])
    corpus = " ".join(str(x) for x in pics + urls).lower()
    findings = []
    done = 0
    for p in (promises or []):
        keywords = [w for w in str(p).lower().split() if len(w) > 3]
        hit = any(k in corpus for k in keywords) if keywords else False
        if hit:
            done += 1
        findings.append({"promise": p, "found": hit})
    pct = round(100.0 * done / len(promises), 1) if promises else 0.0
    return {"compliance_pct": pct, "compliance": pct, "score": pct, "findings": findings}
