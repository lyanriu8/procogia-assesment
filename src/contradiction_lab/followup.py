"""Grounded follow-up questions about one completed run.

The model sees only that run's papers, findings (verified and excluded),
comparisons, verification decisions and quoted passages. Code then checks that
every citation belongs to the run; ungrounded answers are replaced, not shown.
"""

from pydantic import Field

from .schemas import Contract

NOT_ANSWERABLE = (
    "This run's evidence does not answer that. Start a new investigation to search for it."
)
UNGROUNDED = (
    "The model's answer cited evidence that is not part of this run, so it was withheld."
)


class FollowUpAnswer(Contract):
    answerable: bool = Field(
        description="False if the supplied run evidence cannot answer the question."
    )
    answer: str = Field(
        description="Two to five sentences using only the supplied evidence; empty if not answerable."
    )
    cited_claim_ids: list[str] = Field(
        description="claim_id values the answer relies on.", max_length=8
    )
    cited_passage_ids: list[str] = Field(
        description="passage_id values the answer relies on.", max_length=8
    )


TASK = (
    "Answer a follow-up question about ONE completed evidence comparison, using ONLY the supplied run. "
    "Do not use outside knowledge, do not add studies, numbers or mechanisms that are not in the passages, "
    "and do not give personal training or medical advice; describe what these papers report. "
    "Distinguish verified findings from excluded ones, and note that comparison labels are rule-based. "
    "Answer ONLY follow_up_question; previous_turns are background, never repeat an earlier answer. "
    "Put claim_id and passage_id values in the citation fields only; never write IDs in the answer text, refer to papers by first author and year. "
    "If every claim has in_report true, say that all extracted findings passed verification and none were excluded. Never mention internal field names such as in_report, claim_id or passage_id. "
    "If the run cannot answer, set answerable false, leave answer empty and cite nothing."
)


def run_context(result: dict) -> dict:
    report = result["report"]
    verified = {claim["claim_id"] for claim in report["claims"]}
    status = {v["claim_id"]: v for v in report["verification_results"]}
    papers = {
        paper["paper_id"]: {
            "paper_id": paper["paper_id"],
            "title": paper["title"],
            "year": paper.get("publication_year"),
            "first_author": (paper.get("authors") or [None])[0],
            "design": [
                p.split(":", 1)[1]
                for p in paper.get("provenance", [])
                if p.startswith("publication_type:")
            ],
        }
        for paper in report["papers"]
    }
    claims = []
    for claim in result.get("extracted_claims") or report["claims"]:
        check = status.get(claim["claim_id"], {})
        claims.append(
            {
                "claim_id": claim["claim_id"],
                "paper_id": claim["paper_id"],
                "statement": claim["statement"],
                "exposure": claim.get("intervention_or_exposure"),
                "outcome": claim.get("outcome"),
                "direction": claim.get("direction"),
                "design": claim.get("method"),
                "duration": claim.get("duration"),
                "conditions": claim.get("conditions"),
                "verification": check.get("status", "not_checked"),
                "verification_reason": check.get("reason"),
                "in_report": claim["claim_id"] in verified,
            }
        )
    return {
        "question_asked": report["query"],
        "overall_status": report["overall_status"],
        "papers": list(papers.values()),
        "claims": claims,
        "comparisons": [
            {
                "claim_a_id": c["claim_a_id"],
                "claim_b_id": c["claim_b_id"],
                "label": c["disagreement_type"] or "agreement",
                "explanation": c["explanation"],
                "context_differences": c["context_differences"],
                "notes": c["uncertainty_notes"],
            }
            for c in report["comparisons"]
        ],
        "passages": [
            {"passage_id": p["passage_id"], "paper_id": p["paper_id"], "section": p.get("section"), "text": p["text"]}
            for p in report["passages"]
        ],
        "limitations": report["evidence_limitations"],
    }


def answer_followup(model, result: dict, question: str, history: list[dict]) -> dict:
    if not result.get("report"):
        raise ValueError("Run has no completed report")
    context = run_context(result)
    context["papers_by_label"] = {
        p["paper_id"]: f"{(p['first_author'] or p['paper_id']).split(' ')[-1]} {p['year'] or ''}".strip()
        for p in context["papers"]
    }
    context["previous_turns"] = [
        {"question": turn["question"], "answer": turn["answer"]} for turn in history[-3:]
    ]
    context["follow_up_question"] = question
    reply = model.structured(FollowUpAnswer, TASK, context)
    claim_ids = {claim["claim_id"] for claim in context["claims"]}
    passage_ids = {passage["passage_id"] for passage in context["passages"]}
    cited_claims = list(dict.fromkeys(reply.cited_claim_ids))
    cited_passages = list(dict.fromkeys(reply.cited_passage_ids))
    foreign = [i for i in cited_claims if i not in claim_ids] + [
        i for i in cited_passages if i not in passage_ids
    ]
    if not reply.answerable or not reply.answer.strip():
        outcome = {"status": "not_answerable", "answer": NOT_ANSWERABLE, "cited_claim_ids": [], "cited_passage_ids": []}
    elif foreign or not (cited_claims or cited_passages):
        outcome = {"status": "withheld", "answer": UNGROUNDED, "cited_claim_ids": [], "cited_passage_ids": [], "rejected_citations": foreign}
    else:
        outcome = {"status": "grounded", "answer": reply.answer.strip(), "cited_claim_ids": cited_claims, "cited_passage_ids": cited_passages}
    usage = model.usage[-1] if model.usage else {}
    return {
        "question": question,
        **outcome,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }
