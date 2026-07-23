"""
models.py — Pydantic models for data validation and API contracts.

Phase 1: Core data models for the disease tree and symptom vocabulary.
Phase 2+: ScoringResult, QueryRequest, QueryResponse will be fleshed out.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Symptom vocabulary
# ---------------------------------------------------------------------------

class SymptomEntry(BaseModel):
    """A single entry in the closed symptom vocabulary."""
    tag: str = Field(..., description="Machine-readable symptom identifier (e.g. 'resting_tremor')")
    plain_label: str = Field(..., description="Human-readable description")


# ---------------------------------------------------------------------------
# Disease tree
# ---------------------------------------------------------------------------

class Variant(BaseModel):
    """A clinical variant of a disease."""
    name: str
    notes: str = ""


class DiseaseNode(BaseModel):
    """
    Full disease representation matching the JSON source-of-truth schema.
    Used for both data validation at build time and API responses.
    """
    id: str
    name_clinical: str
    name_plain: str
    pathognomonic_symptoms: list[str] = Field(
        default_factory=list,
        description="Defining/near-certain symptom indicators for this disease",
    )
    supporting_symptoms: list[str] = Field(
        default_factory=list,
        description="Common but non-specific symptom indicators",
    )
    variants: list[Variant] = Field(default_factory=list)
    treatments: list[str] = Field(default_factory=list)
    source: str = ""
    clinical_review_status: str = "unreviewed"


# ---------------------------------------------------------------------------
# Scoring (Phase 2)
# ---------------------------------------------------------------------------

class ScoringResult(BaseModel):
    """Result of the deterministic scoring engine for a single disease."""
    disease_id: str
    confidence_pct: int = Field(
        ..., ge=0, le=100,
        description="Deterministic confidence percentage (0-100)",
    )
    pathognomonic_matches: list[str] = Field(default_factory=list)
    supporting_matches: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API contracts (Phase 5)
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """Incoming query from the Flutter app via POST /analyze."""
    text: str = Field(..., description="User's symptom description in natural language")


class CandidateResponse(BaseModel):
    """A single scored disease candidate in the API response."""
    disease_id: str
    name_plain: str
    confidence_pct: int = Field(..., ge=0, le=100)
    pathognomonic_matches: list[str] = Field(default_factory=list)
    supporting_matches: list[str] = Field(default_factory=list)
    variants: list[Variant] = Field(default_factory=list)
    treatments: list[str] = Field(default_factory=list)
    source: str = ""
    clinical_review_status: str = "unreviewed"


class QueryResponse(BaseModel):
    """Response sent back to the Flutter app."""
    status: str = Field(
        ...,
        description="'OK' or 'NO_VERIFIED_DATA'",
    )
    reason: str = Field(
        default="",
        description="Reason for NO_VERIFIED_DATA: 'no_recognized_symptoms' or 'no_matching_disease_nodes'",
    )
    extracted_symptoms: list[str] = Field(
        default_factory=list,
        description="Symptom tags extracted from user input by the LLM parser",
    )
    candidates: list[CandidateResponse] = Field(default_factory=list)
