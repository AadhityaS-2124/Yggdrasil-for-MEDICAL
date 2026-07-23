"""
search_service.py — Symptom tag -> candidate disease lookup + scoring.

Phase 3 implementation: exact-match against the closed vocabulary.
This is legitimate for v1 because the vocabulary is small (39 tags) and closed —
exact matching is more debuggable and equally correct at this scale.

TurboVec / real embeddings can be swapped in later without changing downstream
contracts, since this module's job is just:
  input:  list of symptom tags
  output: scored candidate disease list, or "NO_VERIFIED_DATA"
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

import db
from scoring_engine import score_disease


def find_candidates(
    user_symptom_tags: list[str],
    db_path: Optional[Path] = None,
) -> list[dict]:
    """
    Find all diseases that have ANY symptom overlap with the user's tags.

    Args:
        user_symptom_tags: Symptom tags extracted from user input.
        db_path: Optional path to SQLite DB. Defaults to data/neuro_branch_tree.db.

    Returns:
        List of candidate dicts, each containing:
            - disease_id: str
            - pathognomonic_matches: int
            - supporting_matches: int
            - total_pathognomonic: int
            - total_supporting: int

        Filtered: diseases with zero total matches are excluded.
        Sorted: by pathognomonic_matches desc, then supporting_matches desc.
    """
    if not user_symptom_tags:
        return []

    user_set = set(user_symptom_tags)
    conn = db.get_connection(db_path)

    try:
        all_diseases = db.get_all_diseases(conn)
        candidates = []

        for disease in all_diseases:
            disease_id = disease["id"]
            symptoms = db.get_disease_symptoms(conn, disease_id)

            pathognomonic_set = set(symptoms["pathognomonic"])
            supporting_set = set(symptoms["supporting"])

            pathognomonic_matches = len(pathognomonic_set & user_set)
            supporting_matches = len(supporting_set & user_set)

            # Filter out diseases with zero overlap
            if pathognomonic_matches == 0 and supporting_matches == 0:
                continue

            candidates.append({
                "disease_id": disease_id,
                "pathognomonic_matches": pathognomonic_matches,
                "supporting_matches": supporting_matches,
                "total_pathognomonic": len(pathognomonic_set),
                "total_supporting": len(supporting_set),
            })

        # Sort: pathognomonic matches first, then supporting matches
        candidates.sort(
            key=lambda c: (c["pathognomonic_matches"], c["supporting_matches"]),
            reverse=True,
        )

        return candidates

    finally:
        conn.close()


def search_and_score(
    user_symptom_tags: list[str],
    db_path: Optional[Path] = None,
) -> list[dict] | str:
    """
    Find candidates and score them using the deterministic scoring engine.

    Args:
        user_symptom_tags: Symptom tags extracted from user input.
        db_path: Optional path to SQLite DB.

    Returns:
        - "NO_VERIFIED_DATA" (literal string) if no candidates found.
        - Otherwise, list of dicts sorted by confidence_pct descending:
            - disease_id: str
            - confidence_pct: int (0-100)
    """
    candidates = find_candidates(user_symptom_tags, db_path)

    if not candidates:
        return "NO_VERIFIED_DATA"

    conn = db.get_connection(db_path)
    try:
        results = []
        for candidate in candidates:
            disease_id = candidate["disease_id"]
            symptoms = db.get_disease_symptoms(conn, disease_id)

            confidence_pct = score_disease(
                pathognomonic_symptoms=symptoms["pathognomonic"],
                supporting_symptoms=symptoms["supporting"],
                user_symptoms=user_symptom_tags,
            )

            results.append({
                "disease_id": disease_id,
                "confidence_pct": confidence_pct,
            })

        # Sort by confidence descending
        results.sort(key=lambda r: r["confidence_pct"], reverse=True)

        return results

    finally:
        conn.close()
