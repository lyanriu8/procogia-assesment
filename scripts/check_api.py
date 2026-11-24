"""Live HTTP smoke check; requires the local server and real Ollama models."""

import json
import time
import urllib.request
from pathlib import Path

base = "http://127.0.0.1:8000"


def get(path):
    with urllib.request.urlopen(base + path, timeout=10) as response:
        return json.load(response)


assert get("/readiness")["ready"]
assert get("/health")["model_backend"] == "ollama"
request = urllib.request.Request(
    base + "/research/jobs",
    data=json.dumps(
        {
            "query": "Does it work?",
            "workflow": "dynamic",
            "max_papers": 3,
            "min_comparable_pairs": 1,
        }
    ).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=10) as response:
    assert response.status == 202
    job = json.load(response)
print("Live API job accepted:", job["run_id"], flush=True)
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    result = get("/research/" + job["run_id"])
    if result["status"] not in {"queued", "running"}:
        break
    time.sleep(0.5)
assert result["status"] == "insufficient_evidence", result
assert result["report"]["clarification_question"]
assert result["config"]["max_papers"] == 3
assert result["config"]["min_comparable_pairs"] == 1
assert sum(t["input_tokens"] for t in result["trace"]) > 0
Path("artifacts/api-smoke.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    "PASS: actual HTTP job, actual model inference, progress, persisted result, clarification, and request overrides.",
    flush=True,
)
