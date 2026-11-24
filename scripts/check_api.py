"""Live HTTP smoke check; requires the local server and real Ollama models."""

import json
import time
import urllib.request
from pathlib import Path

base = "http://127.0.0.1:8000"


def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


assert call("/api/system/readiness")["ready"]
assert len(call("/api/articles")) >= 7
session = call("/api/sessions", {"query": "Does it work?", "workflow": "dynamic", "max_papers": 3})
print("Session started:", session["session_id"], flush=True)
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    session = call(f"/api/sessions/{session['session_id']}")
    if session["state"] != "researching":
        break
    time.sleep(0.5)
assert session["state"] == "needs_clarification", session
run = call(f"/api/runs/{session['run_id']}")
assert run["report"]["clarification_question"] and run["report"]["suggested_questions"]
assert run["config"]["max_papers"] == 3
assert sum(t["input_tokens"] for t in run["trace"]) > 0
Path("artifacts/api-smoke.json").write_text(json.dumps({"session": session, "run": run}, indent=2) + "\n")
print("PASS: session created, real inference, clarification with suggestions, persisted run.", flush=True)
