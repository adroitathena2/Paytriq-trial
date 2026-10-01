"""Tests for reply classifier (negotiation / gmail interrupt).

Expected: classify_reply(text) -> one of interested/pushback/yes/no
Defensive: skips if backend missing.
"""
import importlib

import pytest


def _load_classifier():
    candidates = [
        "backend.agents.a3_negotiator",
        "backend.agents.a3",
        "backend.agents.a5_followup",
        "backend.agents.a5",
        "backend.agents.classifier",
        "backend.tools.gmail",
        "backend.utils.classifier",
        "backend.classifier",
    ]
    fn_names = ["classify_reply", "classify", "parse_reply", "label_reply"]
    for mod_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        for fn in fn_names:
            if hasattr(mod, fn) and callable(getattr(mod, fn)):
                return getattr(mod, fn), f"{mod_name}.{fn}"
    return None, None


def _norm(label):
    if not isinstance(label, str):
        # unwrap dict / object
        if isinstance(label, dict):
            for k in ("label", "intent", "category", "result"):
                if k in label and isinstance(label[k], str):
                    return label[k].lower().strip()
            return str(label).lower()
        for attr in ("label", "intent", "category"):
            if hasattr(label, attr):
                v = getattr(label, attr)
                if isinstance(v, str):
                    return v.lower().strip()
        return str(label).lower()
    return label.lower().strip()


def test_pushback_half_budget():
    fn, _ = _load_classifier()
    if fn is None:
        pytest.skip("classifier backend missing, skipping")
    out = _norm(fn("Love it but we only have half the budget, can you reduce price?"))
    assert out == "pushback", f"expected pushback, got {out}"


def test_yes_agreed():
    fn, _ = _load_classifier()
    if fn is None:
        pytest.skip("classifier backend missing, skipping")
    out = _norm(fn("Yes agreed, let's sign the MoU."))
    assert out == "yes", f"expected yes, got {out}"


def test_interested_tell_more():
    fn, _ = _load_classifier()
    if fn is None:
        pytest.skip("classifier backend missing, skipping")
    out = _norm(fn("Sounds interesting, please share more details on footfall and ROI."))
    assert out == "interested", f"expected interested, got {out}"


def test_no_not_interested():
    fn, _ = _load_classifier()
    if fn is None:
        pytest.skip("classifier backend missing, skipping")
    out = _norm(fn("No, not interested at this time. Please don't follow up."))
    assert out == "no", f"expected no, got {out}"
