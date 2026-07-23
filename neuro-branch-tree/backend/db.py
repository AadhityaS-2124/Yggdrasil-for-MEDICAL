"""
db.py — SQLite connection helpers and query functions.

Provides the data access layer for the scoring engine and API.
All queries operate on the SQLite database built by data/build_db.py.
"""

import sqlite3
from pathlib import Path
from typing import Optional

# Default DB path: data/neuro_branch_tree.db relative to project root
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "neuro_branch_tree.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Return a SQLite connection with Row factory enabled.
    
    Args:
        db_path: Path to the SQLite database file. Defaults to data/neuro_branch_tree.db.
    """
    path = db_path or _DEFAULT_DB_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Database not found at {path}. Run 'python data/build_db.py' first."
        )
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def get_all_diseases(conn: sqlite3.Connection) -> list[dict]:
    """Return all diseases as a list of dicts."""
    rows = conn.execute(
        "SELECT id, name_clinical, name_plain, source, clinical_review_status FROM diseases"
    ).fetchall()
    return [dict(row) for row in rows]


def get_disease_by_id(conn: sqlite3.Connection, disease_id: str) -> Optional[dict]:
    """Return a single disease by ID, or None if not found."""
    row = conn.execute(
        "SELECT id, name_clinical, name_plain, source, clinical_review_status "
        "FROM diseases WHERE id = ?",
        (disease_id,),
    ).fetchone()
    return dict(row) if row else None


def get_disease_symptoms(conn: sqlite3.Connection, disease_id: str) -> dict[str, list[str]]:
    """
    Return symptom tags for a disease, grouped by type.
    
    Returns:
        {"pathognomonic": ["tag1", ...], "supporting": ["tag2", ...]}
    """
    rows = conn.execute(
        "SELECT symptom_tag, symptom_type FROM disease_symptoms WHERE disease_id = ?",
        (disease_id,),
    ).fetchall()
    result: dict[str, list[str]] = {"pathognomonic": [], "supporting": []}
    for row in rows:
        result[row["symptom_type"]].append(row["symptom_tag"])
    return result


def get_disease_variants(conn: sqlite3.Connection, disease_id: str) -> list[dict]:
    """Return all variants for a disease."""
    rows = conn.execute(
        "SELECT name, notes FROM variants WHERE disease_id = ?",
        (disease_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_disease_treatments(conn: sqlite3.Connection, disease_id: str) -> list[str]:
    """Return all treatment strings for a disease."""
    rows = conn.execute(
        "SELECT treatment FROM treatments WHERE disease_id = ?",
        (disease_id,),
    ).fetchall()
    return [row["treatment"] for row in rows]


def get_symptom_vocabulary(conn: sqlite3.Connection) -> dict[str, str]:
    """Return the full closed vocabulary as {tag: plain_label}."""
    rows = conn.execute(
        "SELECT tag, plain_label FROM symptom_vocabulary"
    ).fetchall()
    return {row["tag"]: row["plain_label"] for row in rows}


def find_diseases_by_symptoms(conn: sqlite3.Connection, symptom_tags: list[str]) -> list[str]:
    """
    Return disease IDs that have ANY overlap with the given symptom tags.
    
    This is a simple set-overlap search — returns every disease that has
    at least one matching symptom (pathognomonic or supporting).
    Ordering/ranking is left to the scoring engine.
    """
    if not symptom_tags:
        return []
    placeholders = ",".join("?" for _ in symptom_tags)
    rows = conn.execute(
        f"SELECT DISTINCT disease_id FROM disease_symptoms "
        f"WHERE symptom_tag IN ({placeholders})",
        symptom_tags,
    ).fetchall()
    return [row["disease_id"] for row in rows]


def get_full_disease_node(conn: sqlite3.Connection, disease_id: str) -> Optional[dict]:
    """
    Return a complete disease node with symptoms, variants, and treatments.
    Returns None if disease_id not found.
    """
    disease = get_disease_by_id(conn, disease_id)
    if not disease:
        return None
    disease["symptoms"] = get_disease_symptoms(conn, disease_id)
    disease["variants"] = get_disease_variants(conn, disease_id)
    disease["treatments"] = get_disease_treatments(conn, disease_id)
    return disease
