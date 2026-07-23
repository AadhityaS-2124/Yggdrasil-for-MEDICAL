"""
main.py — FastAPI app entrypoint.

Phase 5: Wires parser -> search -> scoring -> DB into a single /analyze endpoint.
Implements the NO_VERIFIED_DATA fallback explicitly at two checkpoints:
  1. Parser returns empty → no recognized symptoms
  2. Search returns no candidates → no matching disease nodes

Architecture flow:
  POST /analyze {"text": "..."}
    → parser_service.parse_symptoms(text) → validated symptom tags
    → search_service.search_and_score(tags) → scored candidates
    → db.get_full_disease_node() → full disease details per candidate
    → JSON response with confidence_pct from deterministic scoring
"""

import sys
from pathlib import Path

# Ensure backend modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException

import db
import parser_service
import search_service
from models import (
    CandidateResponse,
    QueryRequest,
    QueryResponse,
    Variant,
)

app = FastAPI(
    title="Neurology Branching Tree",
    description="Local-first neurology symptom analysis — deterministic scoring, no cloud.",
    version="0.1.0",
)


@app.post("/analyze", response_model=QueryResponse)
def analyze(request: QueryRequest) -> QueryResponse:
    """
    Analyze natural language symptom input and return scored disease candidates.

    Flow:
        1. Validate input (reject empty/whitespace)
        2. Parse symptoms via LLM (closed-vocabulary enforcement)
        3. Search & score candidates (deterministic formula)
        4. Fetch full disease details for each candidate
        5. Return structured response

    Returns NO_VERIFIED_DATA at two explicit checkpoints — never guesses.
    """
    # --- Step 0: Input validation (reject empty before LLM call) ---
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text field must not be empty or whitespace-only.",
        )

    # --- Step 1: Parse symptoms via LLM ---
    extracted_symptoms = parser_service.parse_symptoms(request.text)

    # --- Checkpoint 1: Empty parse → NO_VERIFIED_DATA ---
    if not extracted_symptoms:
        return QueryResponse(
            status="NO_VERIFIED_DATA",
            reason="no_recognized_symptoms",
            extracted_symptoms=[],
            candidates=[],
        )

    # --- Step 2: Search & score ---
    score_result = search_service.search_and_score(extracted_symptoms)

    # --- Checkpoint 2: No candidates → NO_VERIFIED_DATA ---
    if score_result == "NO_VERIFIED_DATA":
        return QueryResponse(
            status="NO_VERIFIED_DATA",
            reason="no_matching_disease_nodes",
            extracted_symptoms=extracted_symptoms,
            candidates=[],
        )

    # --- Step 3: Fetch full disease details for each candidate ---
    conn = db.get_connection()
    try:
        candidates = []
        for scored in score_result:
            disease_id = scored["disease_id"]
            node = db.get_full_disease_node(conn, disease_id)
            if node is None:
                continue  # Shouldn't happen, but defensive

            # Compute which symptoms actually matched for this disease
            user_set = set(extracted_symptoms)
            path_matches = [s for s in node["symptoms"]["pathognomonic"] if s in user_set]
            supp_matches = [s for s in node["symptoms"]["supporting"] if s in user_set]

            candidates.append(CandidateResponse(
                disease_id=disease_id,
                name_plain=node["name_plain"],
                confidence_pct=scored["confidence_pct"],
                pathognomonic_matches=path_matches,
                supporting_matches=supp_matches,
                variants=[Variant(name=v["name"], notes=v.get("notes", "")) for v in node["variants"]],
                treatments=node["treatments"],
                source=node["source"],
                clinical_review_status=node["clinical_review_status"],
            ))

        return QueryResponse(
            status="OK",
            extracted_symptoms=extracted_symptoms,
            candidates=candidates,
        )
    finally:
        conn.close()


@app.get("/health")
def health():
    """Basic health check."""
    return {"status": "ok"}
