"""
Phase 7 integration test — real end-to-end through the running stack.
Tests 4 scenarios through the actual FastAPI backend + Ollama.
"""
import json
import urllib.request
import sys
import time

API = "http://localhost:8008/analyze"

def post_analyze(text: str, label: str) -> dict:
    print(f"\n{'='*70}")
    print(f"TEST: {label}")
    print(f"INPUT: \"{text}\"")
    print(f"{'='*70}")
    
    start = time.time()
    req = urllib.request.Request(
        API,
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        elapsed = time.time() - start
        print(f"HTTP {e.code} in {elapsed:.1f}s")
        print(f"Response: {body}")
        return {"error": e.code, "body": body}
    except Exception as e:
        elapsed = time.time() - start
        print(f"ERROR in {elapsed:.1f}s: {e}")
        return {"error": str(e)}
    
    elapsed = time.time() - start
    print(f"Status: {data['status']} (in {elapsed:.1f}s)")
    
    if data.get("reason"):
        print(f"Reason: {data['reason']}")
    
    if data.get("extracted_symptoms"):
        print(f"Extracted symptoms: {data['extracted_symptoms']}")
    
    if data.get("candidates"):
        print(f"\n  {len(data['candidates'])} candidate(s):")
        for i, c in enumerate(data["candidates"]):
            print(f"  [{i+1}] {c['name_plain']} — {c['confidence_pct']}%")
            print(f"      ID: {c['disease_id']}")
            print(f"      Pathognomonic matches: {c.get('pathognomonic_matches', [])}")
            print(f"      Supporting matches: {c.get('supporting_matches', [])}")
            print(f"      Variants: {[v['name'] for v in c.get('variants', [])]}")
            print(f"      Treatments: {c.get('treatments', [])}")
            print(f"      clinical_review_status: {c.get('clinical_review_status', 'MISSING')}")
    else:
        print("  No candidates.")
    
    return data


# --- Scenario 1: Textbook Parkinson's ---
r1 = post_analyze(
    "my grandfather has been shaking a lot when he's just sitting still, "
    "and he moves really slowly now, his arms are stiff",
    "Textbook Parkinson's description"
)

# --- Scenario 2: Vague headache ---
r2 = post_analyze(
    "I have a headache",
    "Genuinely vague complaint"
)

# --- Scenario 3: Unrelated complaint ---
r3 = post_analyze(
    "my elbow itches",
    "Completely unrelated complaint"
)

# --- Scenario 4: Multi-symptom, two possible diseases ---
r4 = post_analyze(
    "I suddenly can't move the right side of my face, my arm feels weak, "
    "and I also have a terrible throbbing headache on one side with nausea "
    "and I'm seeing flashing lights",
    "Multi-symptom: stroke signs + migraine signs"
)

# --- Summary ---
print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"Scenario 1 (Parkinson's): status={r1.get('status', 'ERROR')}, "
      f"candidates={len(r1.get('candidates', []))}")
print(f"Scenario 2 (Headache):    status={r2.get('status', 'ERROR')}, "
      f"candidates={len(r2.get('candidates', []))}")
print(f"Scenario 3 (Elbow):       status={r3.get('status', 'ERROR')}, "
      f"candidates={len(r3.get('candidates', []))}")
print(f"Scenario 4 (Multi):       status={r4.get('status', 'ERROR')}, "
      f"candidates={len(r4.get('candidates', []))}")

# Check all candidates have clinical_review_status
all_reviewed = True
for r in [r1, r2, r3, r4]:
    for c in r.get("candidates", []):
        if c.get("clinical_review_status") != "unreviewed":
            all_reviewed = False
            print(f"  WARNING: {c['disease_id']} has review status: {c.get('clinical_review_status')}")
if all_reviewed:
    print("All candidates carry clinical_review_status='unreviewed' [OK]")
