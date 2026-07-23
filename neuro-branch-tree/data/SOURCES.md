# Data Sources — Neurology Branching Tree

## Disclaimer

**PROOF OF CONCEPT DATASET.** Every disease node in this dataset reflects
widely-taught, textbook-level clinical associations for common/well-known
neurological conditions. The data is included to demonstrate the system
architecture. It has **NOT** been reviewed by a licensed clinician and **must
not** be used for real diagnostic purposes until it is.

Every disease node carries a `clinical_review_status` field (currently
`"unreviewed"` for all entries) and a `source` field citing its provenance.

---

## Per-Disease Sources

| Disease ID | Source |
|---|---|
| `parkinsons_disease` | General neurology textbook consensus (e.g. Adams and Victor's Principles of Neurology) |
| `essential_tremor` | General neurology textbook consensus |
| `ischemic_stroke` | FAST stroke recognition criteria (American Stroke Association) |
| `migraine` | International Classification of Headache Disorders (ICHD-3) |
| `subarachnoid_hemorrhage` | General neurology/neurosurgery textbook consensus |
| `epilepsy_generalized` | General neurology textbook consensus |
| `epilepsy_absence` | General neurology textbook consensus |
| `alzheimers_disease` | General neurology textbook consensus |
| `multiple_sclerosis` | General neurology textbook consensus; McDonald criteria |
| `als` | General neurology textbook consensus |
| `trigeminal_neuralgia` | General neurology textbook consensus |
| `bacterial_meningitis` | General infectious disease/neurology textbook consensus |

## Symptom Vocabulary

The closed symptom vocabulary (`symptom_vocabulary.json`) was derived from the
same textbook sources listed above, covering the defining and supporting
symptoms for each condition in the dataset.

---

*Last updated: 2026-07-18*
