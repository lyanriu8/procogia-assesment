from contradiction_lab.cli import DEMO_QUERY
from contradiction_lab.evaluation.runner import evaluate, score


def test_evaluation_scores_actual_outputs(engine):
    result = engine.run(
        __import__(
            "contradiction_lab.schemas", fromlist=["ResearchRequest"]
        ).ResearchRequest(query=DEMO_QUERY)
    )
    row = score({"case_id": "test", "expected_status": "evidence_found"}, result)
    assert row["passed"] and row["input_tokens"] > 0
    result["report"]["claims"][0]["claim_id"] = "unverified"
    assert not score({"case_id": "bad"}, result)["passed"]


def test_off_topic_check_fails_if_answered_by_clarification():
    from contradiction_lab.evaluation.runner import score

    result = {
        "report": {"verification_results": [], "claims": [], "comparisons": [], "clarification_question": "Hypothetical?"},
        "trace": [{"input_tokens": 10, "output_tokens": 5, "iteration": 0, "latency_ms": 1, "route": None}],
        "config": {"max_iterations": 2}, "status": "insufficient_evidence", "request": {"workflow": "dynamic"},
        "run_id": "r", "errors": [],
    }
    case = {"case_id": "off-topic", "expected_status": "insufficient_evidence", "empty": True, "clarification": False}
    assert not score(case, result)["passed"]
