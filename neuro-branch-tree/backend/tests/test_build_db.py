"""
test_build_db.py — Verify that build_db.py produces a correct SQLite database.

Tests:
  1. build_db.py runs without error
  2. Correct row counts per table
  3. Every symptom tag in disease_symptoms exists in symptom_vocabulary
  4. All diseases have clinical_review_status = 'unreviewed'
  5. db.py query helpers return correct data
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BUILD_SCRIPT = DATA_DIR / "build_db.py"
DB_FILE = DATA_DIR / "neuro_branch_tree.db"
VOCAB_FILE = DATA_DIR / "symptom_vocabulary.json"
DATASET_FILE = DATA_DIR / "neurology_dataset.json"

# Add backend to path so we can import db.py
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def built_db():
    """Run build_db.py once before all tests in this module."""
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"build_db.py failed:\n{result.stderr}\n{result.stdout}"
    assert DB_FILE.exists(), f"Database file not created at {DB_FILE}"
    yield
    # DB file left in place for manual inspection if needed


@pytest.fixture
def conn():
    """Provide a fresh connection per test."""
    c = sqlite3.connect(str(DB_FILE))
    c.row_factory = sqlite3.Row
    yield c
    c.close()


@pytest.fixture
def source_vocab():
    """Load the source vocabulary JSON."""
    with open(VOCAB_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def source_dataset():
    """Load the source dataset JSON."""
    with open(DATASET_FILE, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Row count tests
# ---------------------------------------------------------------------------
class TestRowCounts:
    """Verify the DB has the expected number of rows per table."""

    def test_symptom_vocabulary_count(self, conn, source_vocab):
        count = conn.execute("SELECT COUNT(*) FROM symptom_vocabulary").fetchone()[0]
        expected = len(source_vocab["symptoms"])
        assert count == expected, f"Expected {expected} vocab entries, got {count}"

    def test_diseases_count(self, conn, source_dataset):
        count = conn.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
        expected = len(source_dataset["diseases"])
        assert count == expected, f"Expected {expected} diseases, got {count}"

    def test_disease_symptoms_count(self, conn, source_dataset):
        expected = 0
        for d in source_dataset["diseases"]:
            expected += len(d.get("pathognomonic_symptoms", []))
            expected += len(d.get("supporting_symptoms", []))
        count = conn.execute("SELECT COUNT(*) FROM disease_symptoms").fetchone()[0]
        assert count == expected, f"Expected {expected} disease_symptoms rows, got {count}"

    def test_variants_count(self, conn, source_dataset):
        expected = sum(len(d.get("variants", [])) for d in source_dataset["diseases"])
        count = conn.execute("SELECT COUNT(*) FROM variants").fetchone()[0]
        assert count == expected, f"Expected {expected} variants, got {count}"

    def test_treatments_count(self, conn, source_dataset):
        expected = sum(len(d.get("treatments", [])) for d in source_dataset["diseases"])
        count = conn.execute("SELECT COUNT(*) FROM treatments").fetchone()[0]
        assert count == expected, f"Expected {expected} treatments, got {count}"


# ---------------------------------------------------------------------------
# Data integrity tests
# ---------------------------------------------------------------------------
class TestDataIntegrity:
    """Verify referential integrity and data correctness."""

    def test_all_symptom_tags_in_vocabulary(self, conn):
        """Every symptom_tag in disease_symptoms must exist in symptom_vocabulary."""
        orphans = conn.execute("""
            SELECT ds.disease_id, ds.symptom_tag
            FROM disease_symptoms ds
            LEFT JOIN symptom_vocabulary sv ON ds.symptom_tag = sv.tag
            WHERE sv.tag IS NULL
        """).fetchall()
        assert len(orphans) == 0, (
            f"Found symptom tags not in vocabulary: "
            f"{[(r['disease_id'], r['symptom_tag']) for r in orphans]}"
        )

    def test_all_diseases_unreviewed(self, conn):
        """All diseases must have clinical_review_status = 'unreviewed'."""
        reviewed = conn.execute(
            "SELECT id, clinical_review_status FROM diseases "
            "WHERE clinical_review_status != 'unreviewed'"
        ).fetchall()
        assert len(reviewed) == 0, (
            f"Expected all diseases unreviewed, but found: "
            f"{[(r['id'], r['clinical_review_status']) for r in reviewed]}"
        )

    def test_symptom_types_valid(self, conn):
        """All symptom_type values must be 'pathognomonic' or 'supporting'."""
        invalid = conn.execute(
            "SELECT disease_id, symptom_tag, symptom_type FROM disease_symptoms "
            "WHERE symptom_type NOT IN ('pathognomonic', 'supporting')"
        ).fetchall()
        assert len(invalid) == 0, f"Invalid symptom types: {[dict(r) for r in invalid]}"

    def test_every_disease_has_at_least_one_symptom(self, conn):
        """Each disease should have at least one symptom mapping."""
        diseases_without = conn.execute("""
            SELECT d.id FROM diseases d
            LEFT JOIN disease_symptoms ds ON d.id = ds.disease_id
            WHERE ds.disease_id IS NULL
        """).fetchall()
        assert len(diseases_without) == 0, (
            f"Diseases with no symptoms: {[r['id'] for r in diseases_without]}"
        )

    def test_specific_parkinsons_symptoms(self, conn):
        """Spot-check: Parkinson's must have its known pathognomonic triad."""
        rows = conn.execute(
            "SELECT symptom_tag FROM disease_symptoms "
            "WHERE disease_id = 'parkinsons_disease' AND symptom_type = 'pathognomonic'"
        ).fetchall()
        tags = {r["symptom_tag"] for r in rows}
        expected = {"resting_tremor", "bradykinesia", "rigidity"}
        assert expected == tags, f"Parkinson's pathognomonic: expected {expected}, got {tags}"


# ---------------------------------------------------------------------------
# db.py query helper tests
# ---------------------------------------------------------------------------
class TestDbHelpers:
    """Test the backend/db.py query functions against the built DB."""

    def test_get_all_diseases(self, conn):
        import db
        diseases = db.get_all_diseases(conn)
        assert len(diseases) == 12
        assert all("id" in d for d in diseases)

    def test_get_disease_by_id(self, conn):
        import db
        result = db.get_disease_by_id(conn, "migraine")
        assert result is not None
        assert result["name_clinical"] == "Migraine"

    def test_get_disease_by_id_not_found(self, conn):
        import db
        result = db.get_disease_by_id(conn, "nonexistent_disease")
        assert result is None

    def test_get_disease_symptoms(self, conn):
        import db
        symptoms = db.get_disease_symptoms(conn, "parkinsons_disease")
        assert "pathognomonic" in symptoms
        assert "supporting" in symptoms
        assert "resting_tremor" in symptoms["pathognomonic"]
        assert "shuffling_gait" in symptoms["supporting"]

    def test_get_disease_variants(self, conn):
        import db
        variants = db.get_disease_variants(conn, "ischemic_stroke")
        assert len(variants) == 2
        names = {v["name"] for v in variants}
        assert "Anterior circulation stroke" in names

    def test_get_disease_treatments(self, conn):
        import db
        treatments = db.get_disease_treatments(conn, "migraine")
        assert len(treatments) > 0
        assert any("Triptans" in t for t in treatments)

    def test_get_symptom_vocabulary(self, conn):
        import db
        vocab = db.get_symptom_vocabulary(conn)
        assert len(vocab) == 39  # 39 symptom tags
        assert "resting_tremor" in vocab

    def test_find_diseases_by_symptoms(self, conn):
        import db
        # headache is a supporting symptom for migraine, SAH, and meningitis
        disease_ids = db.find_diseases_by_symptoms(conn, ["headache"])
        assert "migraine" in disease_ids
        assert "bacterial_meningitis" in disease_ids

    def test_find_diseases_by_symptoms_empty(self, conn):
        import db
        result = db.find_diseases_by_symptoms(conn, [])
        assert result == []

    def test_get_full_disease_node(self, conn):
        import db
        node = db.get_full_disease_node(conn, "als")
        assert node is not None
        assert node["name_clinical"] == "Amyotrophic Lateral Sclerosis (ALS)"
        assert "symptoms" in node
        assert "variants" in node
        assert "treatments" in node
        assert "muscle_weakness_progressive" in node["symptoms"]["pathognomonic"]
