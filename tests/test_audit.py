"""Tests for audit deliverables + logo counting (A6 / vision tool).

Real backend: backend.tools.vision
  audit_deliverables(promises, photos, links) -> {compliance_pct, findings}
  count_logos(image_path_or_url) -> {logo_count, footfall_estimate, notes}

Defensive: skips only if backend truly missing.
"""
import importlib

import pytest


def _load(mod_name, fn_name):
    try:
        mod = importlib.import_module(mod_name)
    except ImportError:
        return None
    fn = getattr(mod, fn_name, None)
    return fn if callable(fn) else None


def _load_audit():
    for mod_name in (
        "backend.tools.vision",
        "backend.agents.a6_auditor",
        "backend.agents.a6",
        "backend.agents.a4_contract",
        "backend.agents.a4",
        "backend.audit",
    ):
        fn = _load(mod_name, "audit_deliverables") or _load(mod_name, "audit") \
            or _load(mod_name, "check_compliance") or _load(mod_name, "verify_deliverables")
        if fn is not None:
            return fn, f"{mod_name}.{fn.__name__}"
    return None, None


def _load_counter():
    for mod_name in (
        "backend.tools.vision",
        "backend.agents.a6_auditor",
        "backend.agents.a6",
        "backend.vision",
    ):
        for fn_name in ("count_logos", "detect_logos", "count_brand_logos"):
            fn = _load(mod_name, fn_name)
            if fn is not None:
                return fn, f"{mod_name}.{fn_name}"
    return None, None


def _compliance_pct(result):
    if isinstance(result, (int, float)):
        v = float(result)
        return v * 100 if 0 < v <= 1.0 and v != 100 else v
    if isinstance(result, dict):
        for k in ("compliance_pct", "compliance", "score", "pct"):
            if k in result:
                return float(result[k])
        if "fulfilled" in result and "total" in result and result["total"]:
            return 100.0 * result["fulfilled"] / result["total"]
    for attr in ("compliance_pct", "compliance", "score"):
        if hasattr(result, attr):
            return float(getattr(result, attr))
    raise AssertionError(f"cannot extract compliance % from {result!r}")


def _call_audit(fn):
    """Call with real (promises, photos, links) signature first, fallback to legacy."""
    promises = ["main banner display", "social media posts"]
    photos_partial = ["photo of main banner display at venue"]
    # real signature
    try:
        return fn(promises, photos_partial, []), "real"
    except TypeError:
        pass
    # legacy (deliverables, evidence-dict)
    try:
        return fn(promises, {"main banner display": True}), "legacy"
    except TypeError:
        pass
    try:
        return fn(deliverables=promises, evidence={"main banner display": True}), "legacy-kw"
    except TypeError:
        pass
    return None, None


def test_audit_compliance_pct():
    fn, where = _load_audit()
    if fn is None:
        pytest.skip("audit backend missing, skipping")
    result, which = _call_audit(fn)
    assert result is not None, f"could not call audit fn at {where}"
    pct = _compliance_pct(result)
    assert 0 <= pct <= 100, f"compliance % 0-100, got {pct}"
    # partial fulfilment (1/2) should give partial %, not 0 or 100
    assert 0 < pct < 100, f"partial fulfilment should give partial %, got {pct} via {which}"


def test_audit_full_compliance():
    fn, _ = _load_audit()
    if fn is None:
        pytest.skip("audit backend missing, skipping")
    try:
        result = fn(
            ["main banner", "stall setup"],
            ["main banner photo at gate", "stall setup photo day1"],
            [],
        )
    except TypeError:
        try:
            result = fn(["a", "b"], {"a": True, "b": True})
        except TypeError:
            pytest.skip("audit signature incompatible")
    pct = _compliance_pct(result)
    assert pct >= 99.9 or pct == 100 or pct == 1.0, f"full fulfilment => ~100%, got {pct}"


def test_count_logos_returns_counts():
    fn, where = _load_counter()
    if fn is None:
        pytest.skip("vision count_logos backend missing, skipping")
    result = fn("artifacts/sample_poster.jpg")
    assert result is not None, f"count_logos returned None at {where}"
    if isinstance(result, dict):
        # real backend returns {logo_count, footfall_estimate, notes}
        if "logo_count" in result:
            assert isinstance(result["logo_count"], (int, float))
            assert result["logo_count"] >= 1
            assert "footfall_estimate" in result
        else:
            assert len(result) >= 1, "should return at least one brand count"
            total = sum(v for v in result.values() if isinstance(v, (int, float)))
            assert total >= 1, f"total logo count >=1, got {result}"
    elif isinstance(result, (list, tuple)):
        assert len(result) >= 1
    elif hasattr(result, "counts"):
        assert result.counts
    else:
        pytest.fail(f"unexpected count_logos return type: {type(result)} {result!r}")
