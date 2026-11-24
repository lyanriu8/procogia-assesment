import json
from pathlib import Path

from contradiction_lab.cli import DEMO_QUERY, UNCERTAINTY_QUERY
from contradiction_lab.config import Settings
from contradiction_lab.graph import ResearchEngine
from contradiction_lab.schemas import ResearchRequest


def describe(result):
    return {"status": result["status"], "passages": len(result["retrieved_passage_ids"]),
            "verified_claims": len(result["report"]["claims"]), "comparisons": len(result["report"]["comparisons"]),
            "nodes": len(result["trace"]), "latency_ms": sum(event["latency_ms"] for event in result["trace"]),
            "input_tokens": sum(event["input_tokens"] for event in result["trace"]),
            "routes": [event["route"] for event in result["trace"] if event["route"]], "run_id": result["run_id"]}


if __name__ == "__main__":
    rows = []
    for top_k in (4, 8):
        result = ResearchEngine().run(ResearchRequest(query=DEMO_QUERY, workflow="static", top_k=top_k))
        rows.append({"experiment": "retrieval_top_k", "value": top_k, **describe(result)})
    for iterations in (1, 2):
        result = ResearchEngine().run(ResearchRequest(query=UNCERTAINTY_QUERY, max_iterations=iterations))
        rows.append({"experiment": "adaptive_iterations", "value": iterations, **describe(result)})
    for threshold in (1, 8):
        result = ResearchEngine(Settings(min_comparable_pairs=threshold)).run(ResearchRequest(query=DEMO_QUERY))
        rows.append({"experiment": "min_comparable_pairs", "value": threshold, **describe(result)})
    output = {"warning": "Measured offline replay; local latencies and structural checks are not live LLM quality/cost measurements.", "experiments": rows}
    path = Path("artifacts/settings-experiments.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
