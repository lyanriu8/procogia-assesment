"""Actual LLM evaluation. Behavioral expectations never supply model answers."""

import argparse
import json
import statistics
import time
from pathlib import Path
from ..config import Settings
from ..graph import ResearchEngine
from ..schemas import ResearchRequest, utcnow
from ..cli import DEMO_QUERY, SYNONYM_QUERY, UNCERTAINTY_QUERY

CASES = [
    {
        "case_id": "contextual-disagreement",
        "query": DEMO_QUERY,
        "expected_status": "evidence_found",
        "disagreement": True,
    },
    {
        "case_id": "productivity",
        "query": DEMO_QUERY,
        "expected_status": "evidence_found",
        "minimum_claims": 2,
    },
    {
        "case_id": "ambiguous",
        "query": "Does it work?",
        "expected_status": "insufficient_evidence",
        "clarification": True,
    },
    {
        "case_id": "outside-corpus",
        "query": UNCERTAINTY_QUERY,
        "expected_status": "insufficient_evidence",
        "empty": True,
        "clarification": False,
    },
    {
        "case_id": "missing-information",
        "query": "Does heavier training load increase muscle hypertrophy?",
        "date_to": "2005-12-31",
        "expected_status": "limited_evidence",
    },
    {
        "case_id": "unsupported-claim",
        "query": DEMO_QUERY,
        "fault": "unsupported_claim",
        "rejection": True,
    },
    {
        "case_id": "invalid-citation",
        "query": DEMO_QUERY,
        "fault": "invalid_citation",
        "rejection": True,
    },
    {
        "case_id": "provider-outage",
        "query": DEMO_QUERY,
        "fault": "provider_error",
        "expected_status": "insufficient_evidence",
        "error": "provider_error",
    },
    {
        "case_id": "synonym-discovery",
        "query": SYNONYM_QUERY,
        "expected_status": "evidence_found",
        "minimum_claims": 2,
    },
]


def score(case, result):
    report = result["report"]
    verified = {
        v["claim_id"]
        for v in report["verification_results"]
        if v["status"] == "verified"
    }
    claims = report["claims"]
    checks = {
        "only_verified_in_report": all(c["claim_id"] in verified for c in claims),
        "comparisons_use_verified_claims": all(
            c["claim_a_id"] in verified and c["claim_b_id"] in verified
            for c in report["comparisons"]
        ),
        "actual_model_calls": sum(t["input_tokens"] for t in result["trace"]) > 0,
        "adaptive_budget": max(t["iteration"] for t in result["trace"])
        <= result["config"]["max_iterations"],
    }
    if "expected_status" in case:
        checks["expected_status"] = result["status"] == case["expected_status"]
    if case.get("minimum_claims"):
        checks["minimum_claims"] = len(claims) >= case["minimum_claims"]
    if case.get("clarification") is True:
        checks["clarification"] = bool(report["clarification_question"])
    if case.get("clarification") is False:
        checks["searched_without_clarification"] = not report["clarification_question"]
    if case.get("empty"):
        checks["empty"] = not claims
    if case.get("rejection"):
        checks["rejection"] = any(
            v["status"] == "rejected" for v in report["verification_results"]
        )
    if case.get("disagreement"):
        checks["disagreement"] = any(
            c["disagreement_type"] == "contextual_disagreement"
            for c in report["comparisons"]
        )
    if case.get("error"):
        checks["error"] = any(e["kind"] == case["error"] for e in result["errors"])
    return {
        "case_id": case["case_id"],
        "workflow": result["request"]["workflow"],
        "expected_status": case.get(
            "expected_status",
            "fault contained" if case.get("fault") else "not asserted",
        ),
        "actual_status": result["status"],
        "passed": all(checks.values()),
        "checks": checks,
        "run_id": result["run_id"],
        "verified_claims": len(claims),
        "rejected_claims": sum(
            v["status"] == "rejected" for v in report["verification_results"]
        ),
        "input_tokens": sum(t["input_tokens"] for t in result["trace"]),
        "output_tokens": sum(t["output_tokens"] for t in result["trace"]),
        "latency_ms": sum(t["latency_ms"] for t in result["trace"]),
        "routes": [t["route"] for t in result["trace"] if t["route"]],
        "errors": result["errors"],
    }


def context_experiment(engine, output_dir):
    rows = []
    for context, k in [("compact", 4), ("evidence-rich", 8)]:
        result = engine.run(
            ResearchRequest(
                query=DEMO_QUERY, workflow="static", context_config=context, top_k=k
            )
        )
        (output_dir / f"context-{context}.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
        row = score({"case_id": context}, result)
        rows.append(
            {
                **row,
                "context": context,
                "top_k": k,
                "retrieved_passages": len(result["retrieved_passage_ids"]),
                "hosted_api_cost_usd": 0,
                "total_compute_cost_usd": None,
                "note": "Actual local inference. K and section preferences both change; not a controlled K-only experiment.",
            }
        )
    return rows


def evaluate(
    dataset=None,
    workflow="both",
    output_dir=Path("artifacts/evaluation"),
    settings=None,
    compare_context_configs=True,
    progress=None,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = ResearchEngine(settings or Settings())
    if engine.settings.source != "corpus":
        raise ValueError(
            "The repeatable benchmark requires the bundled public corpus. Live discovery is evaluated separately."
        )
    cases = json.loads(Path(dataset).read_text()) if dataset else CASES
    rows = []
    for case in cases:
        for mode in (["static", "dynamic"] if workflow == "both" else [workflow]):
            if progress:
                progress(
                    {
                        "status": "running",
                        "current_case": case["case_id"],
                        "workflow": mode,
                        "completed": len(rows),
                        "total": len(cases) * (2 if workflow == "both" else 1),
                    }
                )
            fields = {
                k: case[k]
                for k in ("query", "date_from", "date_to", "top_k", "max_iterations")
                if k in case
            }
            result = engine.run(
                ResearchRequest(workflow=mode, **fields), fault=case.get("fault")
            )
            (output_dir / f"{case['case_id']}-{mode}.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            rows.append(score(case, result))
    context = context_experiment(engine, output_dir) if compare_context_configs else []
    summary = {
        "research_runs": len(rows),
        "research_passed": sum(r["passed"] for r in rows),
        "failed_cases": [
            r["case_id"] + ":" + r["workflow"] for r in rows if not r["passed"]
        ],
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "latency_ms_mean": (
            statistics.mean(r["latency_ms"] for r in rows) if rows else None
        ),
        "warning": "Actual Ollama inference; AI-authored behavioral expectations, not independent scientific gold. Verification uses the same model and may share errors. No scientific accuracy claim.",
    }
    result = {
        "dataset_version": "llm-behavior-v2",
        "evaluated_at": utcnow().isoformat(),
        "model": engine.settings.ollama_model,
        "config": engine.settings.model_dump(mode="json"),
        "summary": summary,
        "cases": rows,
        "context_experiment": context,
    }
    (output_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# Actual LLM evaluation",
        "",
        summary["warning"],
        "",
        "| Case | Workflow | Expected | Actual | Passed |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {r['case_id']} | {r['workflow']} | {r['expected_status']} | {r['actual_status']} | {r['passed']} |"
        for r in rows
    ]
    lines += [
        "",
        "## Measured results",
        "",
        "```json",
        json.dumps(summary, indent=2),
        "```",
        "",
        "## Context comparison",
        "",
        "```json",
        json.dumps(context, indent=2),
        "```",
    ]
    (output_dir / "report.md").write_text("\n".join(lines) + "\n")
    engine.store.save_evaluation(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workflow", choices=["static", "dynamic", "both"], default="both"
    )
    parser.add_argument("--config")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/evaluation"))
    args = parser.parse_args()
    print(
        json.dumps(
            evaluate(
                workflow=args.workflow,
                output_dir=args.output_dir,
                settings=Settings.load(args.config),
                compare_context_configs=not args.quick,
            )["summary"],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
