"""
scoring_engine.py — Deterministic probability scoring.

Implements the weighted symptom-match formula from the master plan.
This engine takes ONLY structured symptom tags as input — never touches
LLM output directly, so it can be fully unit-tested in isolation.

Formula:
    pathognomonic_weight = 15
    supporting_weight    = 3

    raw_score = (pathognomonic_matches * 15) + (supporting_matches * 3)
    max_possible_score = (|P| * 15) + (|S| * 3)
    confidence_pct = round((raw_score / max_possible_score) * 100)

    HARD CAP: if pathognomonic_matches == 0 → confidence capped at 5%
    FLOOR:    if confidence_pct == 0 but supporting_matches > 0 → confidence = 1%
"""

PATHOGNOMONIC_WEIGHT = 15
SUPPORTING_WEIGHT = 3


def score_disease(
    pathognomonic_symptoms: list[str],
    supporting_symptoms: list[str],
    user_symptoms: list[str],
) -> int:
    """
    Compute a deterministic confidence percentage for a single disease
    given the user's extracted symptom tags.

    Args:
        pathognomonic_symptoms: The disease's defining/near-certain symptom tags.
        supporting_symptoms:   The disease's common but non-specific symptom tags.
        user_symptoms:         Symptom tags extracted from the user's input.

    Returns:
        Integer percentage (0-100). Guaranteed properties:
        - If no pathognomonic symptoms match, result is capped at 5%.
        - If result would be 0 but there are supporting matches, floor is 1%.
        - A single vague symptom can never produce a high score.
    """
    P = set(pathognomonic_symptoms)
    S = set(supporting_symptoms)
    U = set(user_symptoms)

    pathognomonic_matches = len(P & U)
    supporting_matches = len(S & U)

    raw_score = (pathognomonic_matches * PATHOGNOMONIC_WEIGHT) + (supporting_matches * SUPPORTING_WEIGHT)
    max_possible_score = (len(P) * PATHOGNOMONIC_WEIGHT) + (len(S) * SUPPORTING_WEIGHT)

    if max_possible_score == 0:
        return 0

    confidence_pct = round((raw_score / max_possible_score) * 100)

    # HARD CAP: vague/non-specific symptoms can never exceed 5%
    if pathognomonic_matches == 0:
        confidence_pct = min(confidence_pct, 5)

    # FLOOR: not literally zero when there's SOME overlap
    if confidence_pct == 0 and supporting_matches > 0:
        confidence_pct = 1

    return confidence_pct
