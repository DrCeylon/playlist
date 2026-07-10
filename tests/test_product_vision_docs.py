"""Regression tests for product vision documentation."""

from __future__ import annotations

from pathlib import Path

import pytest

DOCS_ROOT = Path(__file__).resolve().parents[1] / "docs"

REQUIRED_DOCS = (
    "product/RESONANCE_VISION_2030.md",
    "PRODUCT_VISION.md",
    "ROADMAP.md",
    "product/BACKLOG.md",
    "product/ARCHITECTURAL_PREP.md",
    "architecture/TARGET_ARCHITECTURE.md",
    "architecture/ADR-019-resonance-product-tiers.md",
)

TIER_KEYWORDS = ("MVP", "1.0", "2.0", "2030")


@pytest.mark.parametrize("relative_path", REQUIRED_DOCS)
def test_product_vision_doc_exists(relative_path: str):
    path = DOCS_ROOT / relative_path
    assert path.is_file(), f"Missing product doc: {relative_path}"


def test_vision_2030_covers_all_tiers():
    content = (DOCS_ROOT / "product/RESONANCE_VISION_2030.md").read_text(encoding="utf-8")
    for keyword in TIER_KEYWORDS:
        assert keyword in content, f"RESONANCE_VISION_2030.md must mention tier {keyword}"


def test_vision_2030_states_differentiation():
    content = (DOCS_ROOT / "product/RESONANCE_VISION_2030.md").read_text(encoding="utf-8")
    for phrase in ("local-first", "différenci", "SSOT", "provider"):
        assert phrase.lower() in content.lower()


def test_architectural_prep_forbids_speculative_packages():
    content = (DOCS_ROOT / "product/ARCHITECTURAL_PREP.md").read_text(encoding="utf-8")
    assert "YAGNI" in content
    assert "Do **not** create empty" in content or "not** create empty" in content


def test_roadmap_links_to_vision():
    content = (DOCS_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    assert "RESONANCE_VISION_2030" in content
