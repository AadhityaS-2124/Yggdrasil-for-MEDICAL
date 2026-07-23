"""Test what happens when Ollama is down."""
import json
import urllib.request
import urllib.error
import time

API = "http://localhost:8008/analyze"

print("Testing /analyze with Ollama DOWN...")
start = time.time()
req = urllib.request.Request(
    API,
    data=json.dumps({"text": "I have a headache"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        elapsed = time.time() - start
        print(f"HTTP 200 in {elapsed:.1f}s")
        print(json.dumps(data, indent=2))
except urllib.error.HTTPError as e:
    elapsed = time.time() - start
    body = e.read().decode()
    print(f"HTTP {e.code} in {elapsed:.1f}s")
    print(f"Body: {body}")
except urllib.error.URLError as e:
    elapsed = time.time() - start
    print(f"Connection error in {elapsed:.1f}s: {e}")
except Exception as e:
    elapsed = time.time() - start
    print(f"Error in {elapsed:.1f}s: {e}")
