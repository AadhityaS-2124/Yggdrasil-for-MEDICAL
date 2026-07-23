"""
test_scoring_engine.py — Unit tests for the deterministic scoring formula.

Tests use the REAL neurology_dataset.json to pull each disease's symptom lists,
then assert exact expected percentages that were pre-validated independently.

DO NOT adjust expected values to match output — if a test fails, the bug is
in scoring_engine.py, not in these expected values.
"""

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from scoring_engine import score_disease

# Load the real dataset so tests use actual symptom lists
DATASET_FILE = PROJECT_ROOT / "data" / "neurology_dataset.json"
with open(DATASET_FILE, encoding="utf-8") as f:
    _DISEASES = {d["id"]: d for d in json.load(f)["diseases"]}

ALL_DISEASE_IDS = list(_DISEASES.keys())


def score_all(user_symptoms: list[str]) -> dict[str, int]:
    """Score every disease against the given user symptoms."""
    return {
        did: score_disease(
            _DISEASES[did]["pathognomonic_symptoms"],
            _DISEASES[did]["supporting_symptoms"],
            user_symptoms,
        )
        for did in ALL_DISEASE_IDS
    }


# ---------------------------------------------------------------------------
# Test 1: Vague single symptom — "headache"
# ---------------------------------------------------------------------------
class TestVagueHeadache:
    """
    symptoms = ["headache"]
    headache is only a supporting symptom, never pathognomonic.
    Hard cap must force everything <= 5%.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scores = score_all(["headache"])

    def test_migraine_5pct(self):
        assert self.scores["migraine"] == 5

    def test_bacterial_meningitis_5pct(self):
        assert self.scores["bacterial_meningitis"] == 5

    def test_all_others_zero(self):
        for did in ALL_DISEASE_IDS:
            if did not in ("migraine", "bacterial_meningitis"):
                assert self.scores[did] == 0, (
                    f"{did} should be 0%, got {self.scores[did]}%"
                )


# ---------------------------------------------------------------------------
# Test 2: Classic Parkinson's triad
# ---------------------------------------------------------------------------
class TestParkinsonsTriad:
    """
    symptoms = ["resting_tremor", "bradykinesia", "rigidity"]
    All three are pathognomonic for Parkinson's — should score 88%.
    No other disease shares these exact tags.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scores = score_all(["resting_tremor", "bradykinesia", "rigidity"])

    def test_parkinsons_88pct(self):
        assert self.scores["parkinsons_disease"] == 88

    def test_all_others_zero(self):
        for did in ALL_DISEASE_IDS:
            if did != "parkinsons_disease":
                assert self.scores[did] == 0, (
                    f"{did} should be 0%, got {self.scores[did]}%"
                )


# ---------------------------------------------------------------------------
# Test 3: Migraine with aura
# ---------------------------------------------------------------------------
class TestMigraineWithAura:
    """
    symptoms = ["throbbing_headache_unilateral", "visual_aura", "nausea_with_headache"]
    Two pathognomonic (throbbing + aura) + one supporting (nausea) for migraine.
    nausea_with_headache is also supporting for SAH and meningitis → capped at 5%.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scores = score_all(
            ["throbbing_headache_unilateral", "visual_aura", "nausea_with_headache"]
        )

    def test_migraine_79pct(self):
        assert self.scores["migraine"] == 79

    def test_sah_5pct(self):
        assert self.scores["subarachnoid_hemorrhage"] == 5

    def test_bacterial_meningitis_5pct(self):
        assert self.scores["bacterial_meningitis"] == 5

    def test_all_others_zero(self):
        for did in ALL_DISEASE_IDS:
            if did not in ("migraine", "subarachnoid_hemorrhage", "bacterial_meningitis"):
                assert self.scores[did] == 0, (
                    f"{did} should be 0%, got {self.scores[did]}%"
                )


# ---------------------------------------------------------------------------
# Test 4: Stroke FAST signs
# ---------------------------------------------------------------------------
class TestStrokeFAST:
    """
    symptoms = ["sudden_onset", "unilateral_weakness", "facial_droop", "slurred_speech"]
    All four are pathognomonic for ischemic stroke → 91%.
    sudden_onset is also pathognomonic for SAH → 42%.
    unilateral_weakness is supporting for MS → capped at 5%.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scores = score_all(
            ["sudden_onset", "unilateral_weakness", "facial_droop", "slurred_speech"]
        )

    def test_ischemic_stroke_91pct(self):
        assert self.scores["ischemic_stroke"] == 91

    def test_sah_42pct(self):
        assert self.scores["subarachnoid_hemorrhage"] == 42

    def test_multiple_sclerosis_5pct(self):
        assert self.scores["multiple_sclerosis"] == 5

    def test_all_others_zero(self):
        for did in ALL_DISEASE_IDS:
            if did not in ("ischemic_stroke", "subarachnoid_hemorrhage", "multiple_sclerosis"):
                assert self.scores[did] == 0, (
                    f"{did} should be 0%, got {self.scores[did]}%"
                )


# ---------------------------------------------------------------------------
# Test 5: Single supporting symptom
# ---------------------------------------------------------------------------
class TestSingleSupportingSymptom:
    """
    symptoms = ["fatigue_worsens_with_activity"]
    Only a supporting symptom for MS — hard cap at 5%.
    No other disease references this tag.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scores = score_all(["fatigue_worsens_with_activity"])

    def test_multiple_sclerosis_5pct(self):
        assert self.scores["multiple_sclerosis"] == 5

    def test_all_others_zero(self):
        for did in ALL_DISEASE_IDS:
            if did != "multiple_sclerosis":
                assert self.scores[did] == 0, (
                    f"{did} should be 0%, got {self.scores[did]}%"
                )
