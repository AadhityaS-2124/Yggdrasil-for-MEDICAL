# Neurology Branching Tree

> **PROOF OF CONCEPT** — This dataset covers ~12 well-known neurology conditions for architecture demonstration. It is explicitly NOT clinically validated. Every disease node carries `clinical_review_status: "unreviewed"`.

## Architecture

```
Flutter App (Web/APK)
      |
      v
FastAPI local server (localhost:8008)
      |
      +──> Ollama (qwen3:8b) ── text -> JSON symptom tags ONLY
      |
      +──> Exact-match search ── symptom tags -> candidate disease nodes
      |
      +──> SQLite ── candidate nodes -> full disease/variant/treatment data
      |
      +──> Deterministic scoring engine ── nodes + symptoms -> probability %
      |
      v
JSON response -> Flutter renders cascading cards
```

## Non-Negotiable Laws

1. **Probability Trap Guardrail**: Probability is ALWAYS computed by a deterministic formula (15/3 weights). Never let an LLM output a probability number directly. Vague/single symptom → capped at 5%, floor at 1%.
2. **Anti-Hallucination Law**: No matching node → return `NO_VERIFIED_DATA`. No LLM-generated fallback text, ever.
3. **Local LLM does one job**: natural language → JSON array of symptom tags from a fixed, closed vocabulary (39 tags). It never writes advice, never writes probabilities.
4. Dataset is a proof-of-concept. Not clinically validated.

## Phase Status

| Phase | Description | Status |
|---|---|---|
| 1 | Data layer (JSON → SQLite) | Done |
| 2 | Deterministic scoring engine | Done |
| 3 | Search layer (exact-match) | Done |
| 4 | LLM parser (Ollama/Qwen3 8B) | Done |
| 5 | FastAPI orchestration | Done |
| 6 | Flutter frontend | Done |
| 7 | Integration testing | Done |

## Setup & Run (Complete Guide)

### Prerequisites

- **Python 3.11+** (tested on 3.13)
- **Flutter 3.40+** (tested on 3.44.1)
- **Ollama** installed — [download from ollama.com](https://ollama.com)
- **qwen3:8b model** pulled: `ollama pull qwen3:8b`

### Step 1: Build the database

```bash
cd neuro-branch-tree
python data/build_db.py
```

This compiles `data/neurology_dataset.json` and `data/symptom_vocabulary.json` into `data/neuro_branch_tree.db` (SQLite).

### Step 2: Install Python dependencies

```bash
pip install pydantic fastapi uvicorn httpx pytest
```

### Step 3: Start Ollama

```bash
ollama serve
```

Wait until you see "llama-server started" in the output. Verify with:

```bash
ollama list
# Should show: qwen3:8b
```

### Step 4: Start the FastAPI backend

Open a **new terminal**:

```bash
cd neuro-branch-tree/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8008
```

Verify:

```bash
curl http://localhost:8008/health
# Should return: {"status":"ok"}
```

### Step 5: Run the Flutter app

Open a **new terminal**:

```bash
cd neuro-branch-tree/app
flutter run -d chrome
```

Or build and serve the web version:

```bash
cd neuro-branch-tree/app
flutter build web
# Then serve build/web/ with any static file server
```

### Startup order matters

**Ollama → FastAPI → Flutter** (each depends on the previous).

If Ollama isn't running when a query is submitted, the app will return `NO_VERIFIED_DATA` with reason `no_recognized_symptoms` — it degrades gracefully, never crashes.

## Running Tests

### Backend (deterministic — no LLM needed)

```bash
cd neuro-branch-tree
python -m pytest backend/tests/test_build_db.py backend/tests/test_scoring_engine.py backend/tests/test_search_service.py -v
```

### Backend (LLM tests — requires running Ollama)

```bash
python -m pytest backend/tests/test_parser_schema.py -v -s
python -m pytest backend/tests/test_orchestration.py -v -s
```

### Flutter

```bash
cd neuro-branch-tree/app
flutter test
```

### Full suite

```bash
# Backend deterministic (fast)
python -m pytest backend/tests/test_build_db.py backend/tests/test_scoring_engine.py backend/tests/test_search_service.py -v

# Backend LLM (requires Ollama + FastAPI running)
python -m pytest backend/tests/test_parser_schema.py backend/tests/test_orchestration.py -v -s

# Flutter
cd app && flutter test
```

## Project Structure

```
neuro-branch-tree/
├── backend/
│   ├── main.py               # FastAPI app (POST /analyze endpoint)
│   ├── parser_service.py      # Ollama LLM call + vocabulary enforcement
│   ├── search_service.py      # Exact-match symptom → disease lookup
│   ├── scoring_engine.py      # Deterministic confidence formula (15/3 weights)
│   ├── db.py                  # SQLite query helpers
│   ├── models.py              # Pydantic request/response models
│   └── tests/
│       ├── test_build_db.py          # 20 tests: data layer integrity
│       ├── test_scoring_engine.py    # 15 tests: formula verification
│       ├── test_search_service.py    # 7 tests: search + NO_VERIFIED_DATA
│       ├── test_parser_schema.py     # 10 tests: LLM vocab enforcement
│       └── test_orchestration.py     # 15 tests: end-to-end API
├── data/
│   ├── symptom_vocabulary.json       # Closed vocabulary (39 tags)
│   ├── neurology_dataset.json        # 12 diseases, 44 symptoms, 41 treatments
│   ├── build_db.py                   # JSON → SQLite compiler
│   ├── neuro_branch_tree.db          # Compiled SQLite database
│   └── SOURCES.md                    # Per-disease citation log
├── app/                              # Flutter project
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/disease_node.dart
│   │   ├── services/api_client.dart
│   │   ├── state/query_provider.dart
│   │   ├── screens/
│   │   │   ├── input_screen.dart
│   │   │   └── tree_screen.dart
│   │   └── widgets/
│   │       ├── disease_card.dart
│   │       ├── skeleton_card.dart
│   │       ├── probability_badge.dart
│   │       └── processing_log.dart
│   └── test/
│       ├── widget_test.dart          # 7 tests: state transitions
│       └── widget_test_6b.dart       # 15 tests: visual widgets
└── README.md
```
