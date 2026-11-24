"""Record actual-model presentation checks, with complete raw outputs."""

import argparse
import json
from pathlib import Path
from contradiction_lab.config import Settings
from contradiction_lab.graph import ResearchEngine
from contradiction_lab.schemas import ResearchRequest, utcnow
from contradiction_lab.evaluation.runner import score
from contradiction_lab.cli import DEMO_QUERY, UNCERTAINTY_QUERY

parser = argparse.ArgumentParser()
parser.add_argument(
    "--reuse-completed",
    action="store_true",
    help="Explicitly rescore saved completed real-model measurements; never used by the product.",
)
args = parser.parse_args()

out = Path("artifacts/evaluation")
out.mkdir(parents=True, exist_ok=True)
engine = ResearchEngine(Settings())
scenarios = [
    (
        {
            "case_id": "success-static",
            "query": DEMO_QUERY,
            "expected_status": "evidence_found",
            "minimum_claims": 2,
        },
        "static",
        12,
    ),
    (
        {
            "case_id": "success-dynamic",
            "query": DEMO_QUERY,
            "expected_status": "evidence_found",
            "minimum_claims": 2,
            "disagreement": True,
        },
        "dynamic",
        12,
    ),
    (
        {
            "case_id": "ambiguity",
            "query": "Does it work?",
            "expected_status": "insufficient_evidence",
            "clarification": True,
        },
        "dynamic",
        8,
    ),
    (
        {
            "case_id": "uncertainty",
            "query": UNCERTAINTY_QUERY,
            "expected_status": "insufficient_evidence",
            "empty": True,
        },
        "dynamic",
        8,
    ),
    (
        {
            "case_id": "invalid-citation",
            "query": DEMO_QUERY,
            "fault": "invalid_citation",
            "rejection": True,
        },
        "static",
        4,
    ),
    ({"case_id": "compact-context", "query": DEMO_QUERY}, "static", 4),
]
scenarios.insert(
    -1,
    (
        {
            "case_id": "missing-information",
            "query": "Does heavier training load increase muscle hypertrophy?",
            "date_to": "2005-12-31",
            "expected_status": "limited_evidence",
        },
        "dynamic",
        8,
    ),
)
scenarios.insert(
    -1,
    (
        {
            "case_id": "unsupported-claim",
            "query": DEMO_QUERY,
            "fault": "unsupported_claim",
            "rejection": True,
        },
        "static",
        4,
    ),
)
rows = []
context = []
for case, workflow, k in scenarios:
    print("RUN", case["case_id"], flush=True)
    config = "compact" if case["case_id"] == "compact-context" else "evidence-rich"
    saved = out / (case["case_id"] + ".json")
    reused = args.reuse_completed and saved.exists()
    if reused:
        result = json.loads(saved.read_text())
        if result.get("status") in {"running", "queued", "failed", "interrupted"}:
            raise ValueError("Cannot rescore an incomplete measurement")
        print("Rescoring previously measured real run:", result["run_id"], flush=True)
    else:
        paper_limit = (
            7 if case["case_id"] in {"success-static", "compact-context"} else 3
        )
        result = engine.run(
            ResearchRequest(
                query=case["query"],
                workflow=workflow,
                top_k=k,
                context_config=config,
                max_papers=paper_limit,
                date_from=case.get("date_from"),
                date_to=case.get("date_to"),
            ),
            fault=case.get("fault"),
        )
    (out / (case["case_id"] + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    row = score(case, result)
    row["measurement_reused"] = reused
    row["max_papers"] = result["config"]["max_papers"]
    rows.append(row)
    if case["case_id"] in {"success-static", "compact-context"}:
        context.append(
            {
                **row,
                "context": config,
                "top_k": k,
                "retrieved_passages": len(result["retrieved_passage_ids"]),
            }
        )
    summary = {
        "research_runs": len(rows),
        "research_passed": sum(r["passed"] for r in rows),
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "failed_cases": [r["case_id"] for r in rows if not r["passed"]],
        "warning": "Actual local Ollama inference. Behavioral checks, not independently reviewed scientific accuracy. Same-model verification can share errors.",
    }
    payload = {
        "dataset_version": "presentation-validation-gym-v1",
        "evaluated_at": utcnow().isoformat(),
        "model": engine.settings.ollama_model,
        "summary": summary,
        "cases": rows,
        "context_experiment": context,
        "config": engine.settings.model_dump(mode="json"),
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    engine.store.save_evaluation(payload)
    print("RESULT", json.dumps(row), flush=True)
(out / "report.md").write_text(
    "# Actual model presentation checks\n\n"
    + summary["warning"]
    + "\n\n```json\n"
    + json.dumps(payload, indent=2)
    + "\n```\n"
)
print("FINISHED", json.dumps(summary), flush=True)
