#!/usr/bin/env python3
"""
build_db.py — Compile JSON source-of-truth files into SQLite.

Pure deterministic script. No AI, no network calls.
Reads:  symptom_vocabulary.json, neurology_dataset.json
Writes: neuro_branch_tree.db (in this same directory)

Run:
    python data/build_db.py
"""

import json
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent
VOCAB_FILE = DATA_DIR / "symptom_vocabulary.json"
DATASET_FILE = DATA_DIR / "neurology_dataset.json"
DB_FILE = DATA_DIR / "neuro_branch_tree.db"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS symptom_vocabulary (
    tag         TEXT PRIMARY KEY,
    plain_label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diseases (
    id                     TEXT PRIMARY KEY,
    name_clinical          TEXT NOT NULL,
    name_plain             TEXT NOT NULL,
    source                 TEXT NOT NULL,
    clinical_review_status TEXT NOT NULL DEFAULT 'unreviewed'
);

CREATE TABLE IF NOT EXISTS disease_symptoms (
    disease_id   TEXT NOT NULL,
    symptom_tag  TEXT NOT NULL,
    symptom_type TEXT NOT NULL CHECK(symptom_type IN ('pathognomonic', 'supporting')),
    PRIMARY KEY (disease_id, symptom_tag),
    FOREIGN KEY (disease_id)  REFERENCES diseases(id),
    FOREIGN KEY (symptom_tag) REFERENCES symptom_vocabulary(tag)
);

CREATE TABLE IF NOT EXISTS variants (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_id TEXT NOT NULL,
    name       TEXT NOT NULL,
    notes      TEXT,
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

CREATE TABLE IF NOT EXISTS treatments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    disease_id TEXT NOT NULL,
    treatment  TEXT NOT NULL,
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);
"""


def load_vocabulary(path: Path) -> dict[str, str]:
    """Load symptom_vocabulary.json → {tag: plain_label}."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {entry["tag"]: entry["plain_label"] for entry in data["symptoms"]}


def load_dataset(path: Path) -> list[dict]:
    """Load neurology_dataset.json → list of disease dicts."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["diseases"]


def validate_symptoms(diseases: list[dict], vocab: dict[str, str]) -> None:
    """
    Hard-fail if any symptom tag in the dataset is not in the vocabulary.
    This is a data integrity guardrail — catch mismatches at build time.
    """
    errors = []
    for disease in diseases:
        for sym_type in ("pathognomonic_symptoms", "supporting_symptoms"):
            for tag in disease.get(sym_type, []):
                if tag not in vocab:
                    errors.append(
                        f"  Disease '{disease['id']}' → {sym_type} → "
                        f"tag '{tag}' NOT in symptom_vocabulary.json"
                    )
    if errors:
        print("[FAIL] VALIDATION FAILED -- symptom tags not in vocabulary:\n")
        for e in errors:
            print(e)
        sys.exit(1)


def build_database(db_path: Path, vocab: dict[str, str], diseases: list[dict]) -> None:
    """Create SQLite DB from validated data."""
    # Remove existing DB if present (clean rebuild)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    try:
        conn.executescript(SCHEMA_SQL)

        # --- Insert vocabulary ---
        conn.executemany(
            "INSERT INTO symptom_vocabulary (tag, plain_label) VALUES (?, ?)",
            vocab.items(),
        )

        for d in diseases:
            # --- Insert disease ---
            conn.execute(
                "INSERT INTO diseases (id, name_clinical, name_plain, source, clinical_review_status) "
                "VALUES (?, ?, ?, ?, ?)",
                (d["id"], d["name_clinical"], d["name_plain"], d["source"], d["clinical_review_status"]),
            )

            # --- Insert symptoms ---
            for tag in d.get("pathognomonic_symptoms", []):
                conn.execute(
                    "INSERT INTO disease_symptoms (disease_id, symptom_tag, symptom_type) VALUES (?, ?, ?)",
                    (d["id"], tag, "pathognomonic"),
                )
            for tag in d.get("supporting_symptoms", []):
                conn.execute(
                    "INSERT INTO disease_symptoms (disease_id, symptom_tag, symptom_type) VALUES (?, ?, ?)",
                    (d["id"], tag, "supporting"),
                )

            # --- Insert variants ---
            for v in d.get("variants", []):
                conn.execute(
                    "INSERT INTO variants (disease_id, name, notes) VALUES (?, ?, ?)",
                    (d["id"], v["name"], v.get("notes", "")),
                )

            # --- Insert treatments ---
            for t in d.get("treatments", []):
                conn.execute(
                    "INSERT INTO treatments (disease_id, treatment) VALUES (?, ?)",
                    (d["id"], t),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def print_summary(db_path: Path) -> None:
    """Print row counts for each table."""
    conn = sqlite3.connect(str(db_path))
    tables = ["symptom_vocabulary", "diseases", "disease_symptoms", "variants", "treatments"]
    print(f"\n[OK] Database built: {db_path}\n")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:25s} {count:>4} rows")
    conn.close()


def main() -> None:
    print(f"Loading vocabulary from: {VOCAB_FILE}")
    vocab = load_vocabulary(VOCAB_FILE)
    print(f"  -> {len(vocab)} symptom tags loaded")

    print(f"Loading dataset from:    {DATASET_FILE}")
    diseases = load_dataset(DATASET_FILE)
    print(f"  -> {len(diseases)} diseases loaded")

    print("Validating symptom tags against vocabulary...")
    validate_symptoms(diseases, vocab)
    print("  -> All tags valid [OK]")

    print(f"Building SQLite database: {DB_FILE}")
    build_database(DB_FILE, vocab, diseases)

    print_summary(DB_FILE)


if __name__ == "__main__":
    main()
