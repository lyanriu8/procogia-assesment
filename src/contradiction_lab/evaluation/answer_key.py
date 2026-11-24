"""Score research runs against a human-confirmed answer key.

Unlike the behavioural checks (did the system act sensibly?), these metrics ask
whether it was right:
- behaviour: answered, abstained or asked for clarification as expected;
- exposure: each reported finding is filed under the exposure the paper studies;
- direction: the effect direction is accepted by the key, counted only when the
  exposure also matches (a direction is meaningless relative to the wrong exposure);
- pairs, strict: the key pair received the preferred label;
- pairs, lenient: the key pair received any accepted label (a cautious answer);
- required papers: answers include the papers the key says they must.
"""

import json
from importlib.resources import files


def load_key() -> dict:
    return json.loads(
        files("contradiction_lab").joinpath("evaluation/answer_key.json").read_text(encoding="utf-8")
    )


def behaviour(report: dict) -> str:
    if report.get("clarification_question"):
        return "clarify"
    return "answer" if report["claims"] else "abstain"


def score_run(question: dict, result: dict, key: dict) -> dict:
    report = result["report"]
    papers = key["papers"]
    observed = behaviour(report)
    row = {
        "question": question["id"],
        "expected_behaviour": question["expect"],
        "observed_behaviour": observed,
        "behaviour_correct": observed == question["expect"],
        "directions": [],
        "missing_papers": [],
        "pairs": [],
    }
    for claim in report["claims"]:
        label = papers.get(claim["paper_id"])
        accepted = label and label["directions"].get(claim.get("outcome"))
        entry = {"paper": claim["paper_id"], "outcome": claim.get("outcome"), "direction": claim["direction"],
                 "exposure": claim.get("intervention_or_exposure")}
        if not accepted:
            row["directions"].append({**entry, "graded": False})
            continue
        exposure_correct = claim.get("intervention_or_exposure") == label["exposure"]
        row["directions"].append({**entry, "graded": True, "expected": accepted, "expected_exposure": label["exposure"],
                                  "exposure_correct": exposure_correct,
                                  "correct": exposure_correct and claim["direction"] in accepted})
    if question["expect"] == "answer":
        reported = {c["paper_id"] for c in report["claims"]}
        row["missing_papers"] = [p for p in question.get("required_papers", []) if p not in reported]
        by_paper = {c["claim_id"]: c["paper_id"] for c in report["claims"]}
        for pair in question.get("pairs", []):
            found = None
            for comparison in report["comparisons"]:
                members = {by_paper.get(comparison["claim_a_id"]), by_paper.get(comparison["claim_b_id"])}
                if members == {pair["a"], pair["b"]}:
                    found = comparison["disagreement_type"] or "agreement"
            row["pairs"].append({**pair, "observed": found, "strict": found == pair["preferred"],
                                 "lenient": found in pair["accept"]})
    return row


def summarize(rows: list[dict]) -> dict:
    graded = [d for r in rows for d in r["directions"] if d["graded"]]
    pairs = [p for r in rows for p in r["pairs"]]

    def rate(hits, total):
        return {"correct": hits, "total": total, "rate": round(hits / total, 3) if total else None}

    return {
        "behaviour": rate(sum(r["behaviour_correct"] for r in rows), len(rows)),
        "exposure": rate(sum(d["exposure_correct"] for d in graded), len(graded)),
        "direction": rate(sum(d["correct"] for d in graded), len(graded)),
        "pair_strict": rate(sum(p["strict"] for p in pairs), len(pairs)),
        "pair_lenient": rate(sum(p["lenient"] for p in pairs), len(pairs)),
        "required_papers_missing": sum(len(r["missing_papers"]) for r in rows),
        "ungraded_findings": sum(not d["graded"] for r in rows for d in r["directions"]),
    }
