"""Run the raw-articles baseline on the answer-key questions and compare with the pipeline.

Usage: python scripts/score_baseline.py [--repeats N]
Writes artifacts/baseline/results.json and report.md. If artifacts/answer-key/results.json
exists (from scripts/score_answer_key.py), the report includes a side-by-side table.
"""

import argparse
import json
import time
from pathlib import Path

from contradiction_lab.ai.llm import OllamaModel
from contradiction_lab.config import Settings
from contradiction_lab.evaluation.answer_key import load_key, score_run, summarize
from contradiction_lab.evaluation.baseline import run_baseline
from contradiction_lab.rag.corpus import PublicCorpus
from contradiction_lab.schemas import utcnow

parser = argparse.ArgumentParser()
parser.add_argument("--repeats", type=int, default=1)
args = parser.parse_args()

key = load_key()
corpus = PublicCorpus()
# A larger prompt budget so every passage fits; nothing is truncated.
# Reasoning over ~8k tokens of passages takes several minutes on a local 8B model.
model = OllamaModel(Settings(context_tokens=8000, request_timeout=900))
out = Path("artifacts/baseline")
out.mkdir(parents=True, exist_ok=True)
rows = []
for repeat in range(args.repeats):
    for question in key["questions"]:
        started = time.time()
        result = run_baseline(question["query"], model, corpus)
        row = score_run(question, result, key)
        row.update(repeat=repeat, seconds=round(time.time() - started), invented_paper_ids=result["invented_paper_ids"],
                   input_tokens=result["input_tokens"], output_tokens=result["output_tokens"])
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("question", "observed_behaviour", "behaviour_correct", "pairs", "invented_paper_ids", "seconds")}), flush=True)

summary = summarize(rows)
summary["invented_citations"] = sum(len(r["invented_paper_ids"]) for r in rows)
summary["mean_seconds"] = round(sum(r["seconds"] for r in rows) / len(rows), 1)
payload = {"evaluated_at": utcnow().isoformat(), "system": "raw-articles baseline", "key_status": key["status"],
           "model": model.model, "repeats": args.repeats, "summary": summary, "runs": rows}
(out / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

fmt = lambda m: f"{m['correct']}/{m['total']}" if m["total"] else "n/a"
lines = ["# Raw-articles baseline vs pipeline", ""]
if key["status"] != "confirmed":
    lines += ["**Key status: DRAFT.** Labels not yet confirmed by a person; do not report these as accuracy.", ""]
lines += ["The baseline is one model call with every passage from all 11 papers, the same label definitions and domain hints, "
          "reasoning on, and the same name normalization; it has no retrieval, direction review, rule-based labels or verification.", ""]
pipeline_path = Path("artifacts/answer-key/results.json")
pipeline = json.loads(pipeline_path.read_text(encoding="utf-8"))["summary"] if pipeline_path.exists() else None
metrics = [("Behaviour (answer / abstain / clarify)", "behaviour"), ("Exposure of reported findings", "exposure"),
           ("Direction of reported findings", "direction"), ("Key pairs, strict", "pair_strict"), ("Key pairs, lenient", "pair_lenient")]
lines += ["| Metric | Baseline | Pipeline |", "|---|---|---|"]
for name, field in metrics:
    lines.append(f"| {name} | {fmt(summary[field])} | {fmt(pipeline[field]) if pipeline else 'not run'} |")
lines.append(f"| Required papers missing | {summary['required_papers_missing']} | {pipeline['required_papers_missing'] if pipeline else 'not run'} |")
lines.append(f"| Invented citations (papers not in the library) | {summary['invented_citations']} | 0 by construction |")
lines.append(f"| Mean seconds per question | {summary['mean_seconds']} | see answer-key report |")
lines += ["", "| Question | Repeat | Behaviour | Wrong directions | Pair labels | Invented |", "|---|---|---|---|---|---|"]
for r in rows:
    wrong = [f"{d['paper']}={d['direction']}" + ("" if d.get("exposure_correct", True) else f" (filed under {d['exposure']})") for d in r["directions"] if d["graded"] and not d["correct"]]
    verdict = lambda p: "strict ok" if p["strict"] else ("lenient ok" if p["lenient"] else "wrong, expected " + p["preferred"])
    pairs = ", ".join(f"{p['a']}/{p['b']}: {p['observed']} ({verdict(p)})" for p in r["pairs"]) or "-"
    lines.append(f"| {r['question']} | {r['repeat']} | {r['observed_behaviour']} ({'ok' if r['behaviour_correct'] else 'expected ' + r['expected_behaviour']}) | {', '.join(wrong) or '-'} | {pairs} | {', '.join(r['invented_paper_ids']) or '-'} |")
(out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("SUMMARY", json.dumps(summary), flush=True)
