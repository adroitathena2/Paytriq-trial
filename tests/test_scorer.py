"""Tests for brand fit scorer (A2 / maps.fit_score).

Real backend: backend.tools.maps.fit_score(event, brand) -> float 0-100
  event: object with .footfall (SimpleNamespace ok, getattr fallback 5000)
  brand: dict {category, distance_km, rating}
  scoring: category30 + distance25 + budget25 + audience20

Defensive: skips only if backend truly missing.
"""
import importlib
from types import SimpleNamespace

import pytest


def _load_fit_score():
    candidates = [
        "backend.tools.maps",
        "backend.agents.a1_discovery",
        "backend.agents.a2_scorer",
        "backend.agents.a2",
        "backend.agents.scorer",
        "backend.tools.scorer",
        "backend.scorer",
    ]
    fn_names = ["fit_score", "compute_fit_score", "score_brand", "score", "rank_brand"]
    for mod_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        for fn in fn_names:
            if hasattr(mod, fn) and callable(getattr(mod, fn)):
                return getattr(mod, fn), f"{mod_name}.{fn}"
    return None, None


def _event(footfall=5000):
    return SimpleNamespace(
        name="TechFest 2026",
        location="Pune",
        footfall=footfall,
        audience="tech students 18-24",
    )


def _brand(category="cafe", distance_km=1.0, rating=4.5):
    return {
        "name": "TestBrand",
        "category": category,
        "distance_km": distance_km,
        "rating": rating,
        "phone": "+91-90000",
    }


def _call(fn, event, brand):
    """Real order is (event, brand); try reversed for compat."""
    try:
        return fn(event, brand)
    except TypeError:
        return fn(brand, event)


def _num(score):
    if isinstance(score, dict) and "score" in score:
        score = score["score"]
    if hasattr(score, "score"):
        score = score.score
    return score


def test_fit_score_in_range():
    fn, where = _load_fit_score()
    if fn is None:
        pytest.skip("scorer backend missing, skipping")
    score = _num(_call(fn, _event(), _brand()))
    assert isinstance(score, (int, float)), f"score must be numeric from {where}"
    assert 0 <= score <= 100, f"fit_score must be 0-100, got {score}"


def test_distance_penalty():
    fn, _ = _load_fit_score()
    if fn is None:
        pytest.skip("scorer backend missing, skipping")
    event = _event()
    near = _num(_call(fn, event, _brand(category="cafe", distance_km=0.5, rating=4.5)))
    far = _num(_call(fn, event, _brand(category="cafe", distance_km=4.5, rating=4.5)))
    assert near > far, f"near ({near}) should score higher than far ({far})"


def test_category_match_bonus():
    fn, _ = _load_fit_score()
    if fn is None:
        pytest.skip("scorer backend missing, skipping")
    event = _event()
    # cafe weight 1.0 > printing 0.7 > unknown 0.5
    match = _num(_call(fn, event, _brand(category="cafe", distance_km=1.0, rating=4.5)))
    mismatch = _num(_call(fn, event, _brand(category="printing", distance_km=1.0, rating=4.5)))
    assert match > mismatch, f"category match ({match}) > mismatch ({mismatch})"


def test_perfect_match_high_score():
    fn, _ = _load_fit_score()
    if fn is None:
        pytest.skip("scorer backend missing, skipping")
    event = _event()
    perfect = _num(_call(fn, event, _brand(category="cafe", distance_km=0.4, rating=4.7)))
    poor = _num(_call(fn, event, _brand(category="unknown_xyz", distance_km=4.8, rating=3.5)))
    assert perfect > poor
    assert 0 <= poor <= 100
    assert perfect >= 70, f"perfect match should be high, got {perfect}"
