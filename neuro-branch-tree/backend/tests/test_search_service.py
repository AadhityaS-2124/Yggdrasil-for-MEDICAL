"""
test_search_service.py — Tests for the search + scoring pipeline.

Tests confirm:
  1. Known pathognomonic symptom set → correct top candidate + exact confidence_pct
  2. Unknown/invalid tags → zero candidates (no crash), returns NO_VERIFIED_DATA
  3. Single supporting-only symptom → candidate found but low confidence
"""

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from search_service import find_candidates, search_and_score

# DB must already be built (test_build_db.py handles that in its module fixture,
# but we assert the file exists as a safety check)
DB_PATH = PROJECT_ROOT / "data" / "neuro_branch_tree.db"


@pytest.fixture(autouse=True)
def check_db_exists():
    """Ensure the SQLite DB exists before running search tests."""
    assert DB_PATH.exists(), (
        f"Database not found at {DB_PATH}. "
        "Run 'python data/build_db.py' before running these tests."
    )


# ---------------------------------------------------------------------------
# Test 1: Parkinson's triad — pathognomonic exact match
# ---------------------------------------------------------------------------
class TestParkinsonsTriadSearch:
    """
    symptoms = ["resting_tremor", "bradykinesia", "rigidity"]
    All three are pathognomonic for Parkinson's.
    Expected: parkinsons_disease is top result, confidence_pct = 88.
    """

    def test_find_candidates_returns_parkinsons_first(self):
        candidates = find_candidates(
            ["resting_tremor", "bradykinesia", "rigidity"], DB_PATH
        )
        assert len(candidates) > 0
        assert candidates[0]["disease_id"] == "parkinsons_disease"
        assert candidates[0]["pathognomonic_matches"] == 3
        assert candidates[0]["total_pathognomonic"] == 3
        assert candidates[0]["total_supporting"] == 2

    def test_search_and_score_parkinsons_88pct(self):
        results = search_and_score(
            ["resting_tremor", "bradykinesia", "rigidity"], DB_PATH
        )
        assert isinstance(results, list)
        assert len(results) > 0
        # Parkinson's should be the top result with exactly 88%
        top = results[0]
        assert top["disease_id"] == "parkinsons_disease"
        assert top["confidence_pct"] == 88


# ---------------------------------------------------------------------------
# Test 2: Unknown/invalid tags — zero candidates, NO_VERIFIED_DATA
# ---------------------------------------------------------------------------
class TestUnknownTagSearch:
    """
    symptoms = ["itchy_elbow_nonexistent_tag"]
    This tag isn't in the vocabulary or any disease's symptom list.
    search_service.py should NOT crash — it should simply find zero candidates.

    NOTE/TODO: Real input validation (rejecting tags not in symptom_vocabulary.json)
    happens in Phase 4/5 (parser_service.py + main.py orchestration). The search
    layer itself is downstream of that validation. This test just confirms the
    search layer handles unknown tags gracefully — returning zero candidates
    rather than crashing.
    """

    def test_find_candidates_returns_empty(self):
        candidates = find_candidates(
            ["itchy_elbow_nonexistent_tag"], DB_PATH
        )
        assert candidates == []

    def test_search_and_score_returns_no_verified_data(self):
        result = search_and_score(
            ["itchy_elbow_nonexistent_tag"], DB_PATH
        )
        assert result == "NO_VERIFIED_DATA"

    def test_empty_input_returns_no_verified_data(self):
        """Edge case: completely empty symptom list."""
        result = search_and_score([], DB_PATH)
        assert result == "NO_VERIFIED_DATA"


# ---------------------------------------------------------------------------
# Test 3: Single supporting symptom — low confidence, but still a candidate
# ---------------------------------------------------------------------------
class TestSingleSupportingSymptom:
    """
    symptoms = ["swallowing_difficulty"]
    This is a supporting symptom for ALS only.
    ALS should appear as a candidate (not filtered out), but with low confidence
    because:
      - pathognomonic_matches = 0 → hard cap at 5%
      - supporting_matches = 1
      - max_possible_score = (3*15) + (1*3) = 48
      - raw_score = 0 + (1*3) = 3
      - round(3/48 * 100) = round(6.25) = 6 → capped to 5 (hard cap)

    So ALS should be the only candidate, confidence_pct = 5.
    """

    def test_find_candidates_returns_als(self):
        candidates = find_candidates(["swallowing_difficulty"], DB_PATH)
        assert len(candidates) == 1
        assert candidates[0]["disease_id"] == "als"
        assert candidates[0]["pathognomonic_matches"] == 0
        assert candidates[0]["supporting_matches"] == 1

    def test_search_and_score_als_low_confidence(self):
        results = search_and_score(["swallowing_difficulty"], DB_PATH)
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["disease_id"] == "als"
        # Hard cap: pathognomonic_matches == 0, so capped at 5%
        assert results[0]["confidence_pct"] == 5
