import json

with open("data/neurology_dataset.json") as f:
    data = json.load(f)["diseases"]

PATH_W = 15
SUPP_W = 3

def score(disease, user_symptoms):
    P = set(disease["pathognomonic_symptoms"])
    S = set(disease["supporting_symptoms"])
    U = set(user_symptoms)
    path_m = len(P & U)
    supp_m = len(S & U)
    raw = path_m * PATH_W + supp_m * SUPP_W
    max_score = len(P) * PATH_W + len(S) * SUPP_W
    if max_score == 0:
        return 0
    pct = round((raw / max_score) * 100)
    if path_m == 0:
        pct = min(pct, 5)
    if pct == 0 and supp_m > 0:
        pct = 1
    return pct

tests = [
    ("vague headache only", ["headache"]),
    ("classic parkinsons triad", ["resting_tremor", "bradykinesia", "rigidity"]),
    ("migraine with aura", ["throbbing_headache_unilateral", "visual_aura", "nausea_with_headache"]),
    ("stroke fast signs", ["sudden_onset", "unilateral_weakness", "facial_droop", "slurred_speech"]),
    ("single supporting symptom", ["fatigue_worsens_with_activity"]),
]

by_id = {d["id"]: d for d in data}

for label, symptoms in tests:
    print(f"\n--- {label}: {symptoms} ---")
    scores = [(d["id"], score(d, symptoms)) for d in data]
    scores.sort(key=lambda x: -x[1])
    for did, pct in scores[:4]:
        print(f"  {did:30s} {pct}%")
