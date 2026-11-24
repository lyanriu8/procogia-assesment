import argparse
import json
import statistics
import time
from importlib.resources import files
from pathlib import Path

from ..cli import DEMO_QUERY
from ..config import Settings
from ..fixtures import FixtureCorpus
from ..graph import ResearchEngine
from ..retrieval import approximate_tokens
from ..schemas import ResearchRequest, ScientificClaim, utcnow
from ..skills import classify_disagreement
from .metrics import macro_f1, precision_recall_f1


def load_cases(path=None):
    text = Path(path).read_text() if path else files("contradiction_lab").joinpath("data/cases.jsonl").read_text()
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def pair_case(case):
    claims = [ScientificClaim(claim_id=side, paper_id="synthetic-" + side, statement="SYNTHETIC protocol test, not a scientific finding.",
                              evidence_passage_ids=["synthetic-" + side], **case[side]) for side in ("left", "right")]
    comparison = classify_disagreement(*claims)
    prediction = comparison.disagreement_type or "agreement"
    return {"case_id": case["case_id"], "kind": case["kind"], "expected": case["expected"], "predicted": prediction,
            "passed": prediction == case["expected"], "comparison": comparison.model_dump(), "label_status": "synthetic_rule_expectation_not_scientific_gold"}


def score_research(case, result, corpus):
    expected_ids = set(case.get("expected_claims", []))
    expected = {claim.claim_id: claim for claim in corpus.claims if claim.claim_id in expected_ids}
    actual = result["extracted_claims"]
    extraction = precision_recall_f1([(claim["claim_id"], claim["statement"]) for claim in actual],
                                    [(claim.claim_id, claim.statement) for claim in expected.values()])
    expected_passages = {claim.evidence_passage_ids[0] for claim in expected.values()}
    retrieval = len(set(result["retrieved_passage_ids"]) & expected_passages) / len(expected_passages) if expected_passages else None
    fields = ("outcome", "direction", "study_system", "method", "duration", "intervention_or_exposure")
    expected_fields = [(claim.claim_id, field, str(getattr(claim, field))) for claim in expected.values() for field in fields if getattr(claim, field) is not None]
    actual_fields = [(claim["claim_id"], field, str(claim[field])) for claim in actual for field in fields if claim[field] is not None]
    context = precision_recall_f1(actual_fields, expected_fields)
    lookup = {frozenset((comparison["claim_a_id"], comparison["claim_b_id"])): comparison["disagreement_type"] or "agreement"
              for comparison in result["report"]["comparisons"]}
    labels, predicted = [], []
    for left, right, label in case.get("expected_pairs", []):
        labels.append(label)
        predicted.append(lookup.get(frozenset((left, right)), "missing"))
    verification = result["report"]["verification_results"]
    reported_claim_ids = {claim["claim_id"] for claim in result["report"]["claims"]}
    verified_claim_ids = {row["claim_id"] for row in verification if row["status"] == "verified"}
    unsupported = len(reported_claim_ids - verified_claim_ids) / len(reported_claim_ids) if reported_claim_ids else None
    routes = [event["route"] for event in result["trace"] if event["route"]]
    expected_route = case.get("expected_dynamic_route") if result["request"]["workflow"] == "dynamic" else None
    route_ok = routes[0] == expected_route if expected_route else None
    status_ok = result["status"] == case["expected_status"]
    rejection_ok = any(row["status"] == "rejected" for row in verification) if case.get("expect_rejection") else True
    error_ok = any(error["kind"] == case["expected_error"] for error in result["errors"]) if case.get("expected_error") else True
    pairs_ok = labels == predicted
    passed = status_ok and rejection_ok and error_ok and pairs_ok and route_ok is not False
    failure = []
    if not status_ok:
        failure.append("discovery/retrieval" if not result["retrieved_passage_ids"] else "report_synthesis")
    if not pairs_ok:
        failure.append("comparability/classification")
    if route_ok is False:
        failure.append("routing")
    if not rejection_ok:
        failure.append("citation_verification")
    return {
        "case_id": case["case_id"], "kind": "research", "workflow": result["request"]["workflow"], "scenario": case["scenario"],
        "expected_status": case["expected_status"], "actual_status": result["status"], "passed": passed, "failure_components": failure,
        "retrieval_recall_at_k": retrieval, "extraction": extraction, "context_field_f1": context["f1"],
        "classification_expected": labels, "classification_predicted": predicted,
        "citation_source_validity": sum(row["source_resolves"] and row["passage_exists"] for row in verification) / len(verification) if verification else None,
        "passage_support_rate": sum(row["passage_supports_claim"] == "yes" for row in verification) / len(verification) if verification else None,
        "unsupported_report_claim_rate": unsupported, "routing_correct": route_ok, "routes": routes,
        "input_tokens": sum(event["input_tokens"] for event in result["trace"]),
        "output_tokens": sum(event["output_tokens"] for event in result["trace"]),
        "latency_ms": sum(event["latency_ms"] for event in result["trace"]),
        "label_status": "AI_authored_regression_expectations_pending_human_review", "run_id": result["run_id"],
    }


def context_experiment(engine, output_dir):
    corpus = FixtureCorpus()
    cases = load_cases()
    representative = next(case for case in cases if case["case_id"] == "r01-main")
    rows = []
    for context, top_k in (("compact", 4), ("evidence-rich", 8)):
        start = time.perf_counter()
        result = engine.run(ResearchRequest(query=DEMO_QUERY, workflow="static", context_config=context, top_k=top_k))
        score = score_research(representative, result, corpus)
        passage_lookup = {passage.passage_id: passage for passage in corpus.passages}
        context_tokens = sum(approximate_tokens(passage_lookup[identifier].model_dump_json()) for identifier in result["retrieved_passage_ids"])
        rows.append({"context": context, "top_k": top_k, "retrieved_passages": len(result["retrieved_passage_ids"]),
                     "verified_claims": len(result["report"]["claims"]), "context_payload_tokens_approx": context_tokens,
                     "latency_ms": round((time.perf_counter() - start) * 1000, 3), "extraction_f1": score["extraction"]["f1"],
                     "context_field_f1": score["context_field_f1"], "retrieval_recall_at_k": score["retrieval_recall_at_k"],
                     "citation_source_validity": score["citation_source_validity"], "passage_support_rate": score["passage_support_rate"],
                     "classification": macro_f1(score["classification_expected"], score["classification_predicted"]),
                     "unsupported_report_claim_rate": score["unsupported_report_claim_rate"],
                     "llm_input_tokens": score["input_tokens"], "llm_output_tokens": score["output_tokens"],
                     "hosted_api_cost_usd": 0 if engine.settings.model_backend == "replay" else None,
                     "total_compute_cost_usd": None, "cost_note": "Replay has no hosted API calls. Local compute cost is not metered; no live-model quality claim.",
                     "run_id": result["run_id"]})
        (output_dir / f"context-{context}.json").write_text(json.dumps(result, indent=2) + "\n")
    return rows


def evaluate(dataset=None, workflow="both", output_dir=Path("artifacts/evaluation"), settings=None, compare_context_configs=True):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = ResearchEngine(settings or Settings())
    corpus = FixtureCorpus()
    rows = []
    for case in load_cases(dataset):
        if case["kind"] == "synthetic_pair":
            rows.append(pair_case(case))
            continue
        for mode in (["static", "dynamic"] if workflow == "both" else [workflow]):
            request_fields = {field: case[field] for field in ("query", "top_k", "max_iterations", "date_from", "date_to") if field in case}
            result = engine.run(ResearchRequest(workflow=mode, **request_fields), fault=case.get("fault"), paper_subset=case.get("paper_ids"))
            (output_dir / f"{case['case_id']}-{mode}.json").write_text(json.dumps(result, indent=2) + "\n")
            rows.append(score_research(case, result, corpus))
    research_rows = [row for row in rows if row["kind"] == "research"]
    synthetic_rows = [row for row in rows if row["kind"] == "synthetic_pair"]

    def average(field):
        values = [row[field] for row in research_rows if row[field] is not None]
        return statistics.mean(values) if values else None

    expected_labels = [label for row in research_rows for label in row["classification_expected"]]
    predicted_labels = [label for row in research_rows for label in row["classification_predicted"]]
    summary = {
        "research_runs": len(research_rows), "research_passed": sum(row["passed"] for row in research_rows),
        "synthetic_pair_cases": len(synthetic_rows), "synthetic_pair_passed": sum(row["passed"] for row in synthetic_rows),
        "retrieval_recall_at_k_mean": average("retrieval_recall_at_k"),
        "extraction_f1_mean": statistics.mean(row["extraction"]["f1"] for row in research_rows) if research_rows else None,
        "context_field_f1_mean": average("context_field_f1"), "citation_source_validity_mean": average("citation_source_validity"),
        "passage_support_rate_mean": average("passage_support_rate"), "unsupported_report_claim_rate_mean": average("unsupported_report_claim_rate"),
        "routing_accuracy": average("routing_correct"), "latency_ms_mean": average("latency_ms"),
        "classification_real_source_pairs": macro_f1(expected_labels, predicted_labels),
        "classification_synthetic_rules": macro_f1([row["expected"] for row in synthetic_rows], [row["predicted"] for row in synthetic_rows]),
        "failed_cases": [f"{row['case_id']}:{row.get('workflow', 'pair')}" for row in rows if not row["passed"]],
        "warning": "Regression/replay measurements only. Labels are AI-authored, not independently human-reviewed scientific gold. Synthetic pairs are reported separately; small repeated corpus is not generalization evidence.",
    }
    context = context_experiment(engine, output_dir) if compare_context_configs else []
    result = {"dataset_version": "regression-v1", "evaluated_at": utcnow().isoformat(), "config": engine.settings.model_dump(mode="json"),
              "model": "fixture-replay-v1" if engine.settings.model_backend == "replay" else "configured Ollama model",
              "prompt_version": "grounded-v1", "summary": summary, "cases": rows, "context_experiment": context}
    (output_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Evaluation results", "", summary["warning"], "", "```json", json.dumps(summary, indent=2), "```", "",
             "| Case | Workflow | Passed | Expected | Actual | Failure component |", "|---|---|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['case_id']} | {row.get('workflow', 'synthetic')} | {row['passed']} | {row.get('expected_status', row.get('expected'))} | {row.get('actual_status', row.get('predicted'))} | {', '.join(row.get('failure_components', []))} |")
    lines.extend(["", "## Context experiment", "", "```json", json.dumps(context, indent=2), "```", "",
                  "No human scientific quality target is certified by these results. See docs/evaluation.md for denominators and caveats."])
    (output_dir / "report.md").write_text("\n".join(lines) + "\n")
    engine.store.save_evaluation(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset")
    parser.add_argument("--workflow", choices=["static", "dynamic", "both"], default="both")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/evaluation"))
    parser.add_argument("--compare-context-configs", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.dataset, args.workflow, args.output_dir)
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
