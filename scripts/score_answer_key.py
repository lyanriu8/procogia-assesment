"""Run the answer-key questions on the real model and score them.

Usage: python scripts/score_answer_key.py [--repeats N]
Writes artifacts/answer-key/results.json and report.md.
"""

import argparse
import json
import time
from pathlib import Path

from contradiction_lab.ai.research import ResearchService
from contradiction_lab.config import Settings
from contradiction_lab.evaluation.answer_key import load_key, score_run, summarize
from contradiction_lab.schemas import ResearchRequest, utcnow

parser = argparse.ArgumentParser()
parser.add_argument("--repeats", type=int, default=1)
args = parser.parse_args()

key = load_key()
engine = ResearchService(Settings())
out = Path("artifacts/answer-key")
out.mkdir(parents=True, exist_ok=True)
rows = []
for repeat in range(args.repeats):
    for question in key["questions"]:
        started = time.time()
        result = engine.run(ResearchRequest(query=question["query"], workflow="dynamic", max_papers=3))
        row = score_run(question, result, key)
        row.update(repeat=repeat, run_id=result["run_id"], seconds=round(time.time() - started))
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("question", "behaviour_correct", "missing_papers", "pairs", "seconds")}), flush=True)

summary = summarize(rows)
payload = {"evaluated_at": utcnow().isoformat(), "key_status": key["status"], "confirmed_by": key["confirmed_by"],
           "model": engine.settings.ollama_model, "repeats": args.repeats, "summary": summary, "runs": rows}
(out / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

fmt = lambda m: f"{m['correct']}/{m['total']}" if m["total"] else "n/a"
lines = ["# Answer-key evaluation", ""]
if key["status"] != "confirmed":
    lines += ["**Key status: DRAFT.** Labels were drafted by the AI assistant and not yet confirmed by a person; do not report these as accuracy.", ""]
lines += [f"Model {payload['model']}, {args.repeats} repeat(s), {len(rows)} runs, {payload['evaluated_at']}.", "",
          "| Metric | Result |", "|---|---|",
          f"| Behaviour (answer / abstain / clarify) | {fmt(summary['behaviour'])} |",
          f"| Exposure of reported findings | {fmt(summary['exposure'])} |",
          f"| Direction of reported findings (exposure must also match) | {fmt(summary['direction'])} |",
          f"| Key pairs, strict (preferred label) | {fmt(summary['pair_strict'])} |",
          f"| Key pairs, lenient (any accepted label) | {fmt(summary['pair_lenient'])} |",
          f"| Required papers missing from answers | {summary['required_papers_missing']} |",
          f"| Reported findings the key does not cover | {summary['ungraded_findings']} |", "",
          "| Question | Repeat | Behaviour | Wrong directions | Missing papers | Pair labels |", "|---|---|---|---|---|---|"]
for r in rows:
    wrong = [f"{d['paper']}={d['direction']}" + ("" if d["exposure_correct"] else f" (filed under {d['exposure']})") for d in r["directions"] if d["graded"] and not d["correct"]]
    verdict = lambda p: "strict ok" if p["strict"] else ("lenient ok" if p["lenient"] else "wrong, expected " + p["preferred"])
    pairs = ", ".join(f"{p['a']}/{p['b']}: {p['observed']} ({verdict(p)})" for p in r["pairs"]) or "-"
    lines.append(f"| {r['question']} | {r['repeat']} | {r['observed_behaviour']} ({'ok' if r['behaviour_correct'] else 'expected ' + r['expected_behaviour']}) | {', '.join(wrong) or '-'} | {', '.join(r['missing_papers']) or '-'} | {pairs} |")
(out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("SUMMARY", json.dumps(summary), flush=True)
