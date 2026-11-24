"""Raw-articles baseline: one model call with every passage in the library.

This is the "just paste the papers into the model" approach the pipeline is
compared against. To make the comparison about the pipeline (retrieval, staged
extraction, direction review, comparison rules, verification) and nothing else:

- it reads the same passages the pipeline can retrieve, all of them, in one prompt;
- it gets the same label definitions and the same domain hints;
- its findings go through the same name normalization;
- reasoning mode is on and the context window is large enough for everything;
- its answer is converted to the pipeline's report shape and scored by the same
  answer key.

What it does not get: retrieval, separate direction review, rule-based labels,
or verification against the source text.
"""

from typing import Literal

from pydantic import Field

from contradiction_lab.ai.research.skills import normalize_claims
from contradiction_lab.domain import load_domain
from contradiction_lab.schemas import Contract, ScientificClaim

Direction = Literal["positive", "negative", "no_effect", "mixed", "unclear"]
Label = Literal["agreement", "contextual_disagreement", "genuine_contradiction", "apparent_disagreement", "insufficient_evidence"]


class BaselineFinding(Contract):
    paper_id: str
    statement: str = Field(description="The finding, close to the paper's wording.")
    exposure: str = Field(description="What was varied or compared, as a short noun phrase.")
    outcome: str = Field(description="What was measured, as a short noun phrase.")
    direction: Direction = Field(description="How the outcome changes as the exposure INCREASES.")


class BaselinePair(Contract):
    paper_a: str
    paper_b: str
    label: Label


class BaselineAnswer(Contract):
    behaviour: Literal["answer", "abstain", "clarify"] = Field(
        description="answer if the papers address the question; abstain if they do not; clarify if the question is too vague to search."
    )
    clarification_question: str | None
    findings: list[BaselineFinding] = Field(description="One finding per relevant paper; empty unless behaviour is answer.")
    pairs: list[BaselinePair] = Field(description="Every pair of reported findings from different papers.")


INSTRUCTIONS = (
    "You are given a research question and a library of research papers (passages quoted from each). "
    "Answer the question using ONLY these papers. Report one finding per paper that studies what the question asks about; "
    "ignore papers about a different exposure or intervention. If no paper studies what the question asks about, set behaviour to abstain. "
    "If the question names no identifiable exposure and outcome, set behaviour to clarify and write a clarifying question. "
    "Direction is how the outcome changes as the exposure INCREASES (positive, negative, no_effect for no detectable difference, mixed, unclear). "
    "Then label every pair of reported findings from different papers: agreement (same outcome, same direction); "
    "contextual_disagreement (same outcome and exposure, different results, with differences in study context that may explain it, "
    "including one effect versus no detectable effect); genuine_contradiction (opposite directions under matching conditions); "
    "apparent_disagreement (different outcomes or exposures, so not comparable); insufficient_evidence (not enough context to compare). "
    "Use paper_id values exactly as given. "
)


def library_context(corpus) -> list[dict]:
    by_paper = {}
    for passage in corpus.passages:
        by_paper.setdefault(passage.paper_id, []).append(f"[{passage.section}] {passage.text}")
    return [
        {"paper_id": p.paper_id, "title": p.title, "year": p.publication_year, "passages": by_paper.get(p.paper_id, [])}
        for p in corpus.papers
    ]


def run_baseline(question: str, model, corpus) -> dict:
    """One structured call; returns a result in the pipeline's shape plus baseline-only diagnostics."""
    domain = load_domain()
    reply = model.structured(
        BaselineAnswer,
        INSTRUCTIONS + domain.get("extraction_hint", "") + " " + domain.get("direction_example", ""),
        {"research_question": question, "papers": library_context(corpus)},
        think=True,
    )
    known = {p.paper_id for p in corpus.papers}
    invented = sorted({f.paper_id for f in reply.findings if f.paper_id not in known}
                      | {x for pair in reply.pairs for x in (pair.paper_a, pair.paper_b) if x not in known})
    claims, claim_of = [], {}
    if reply.behaviour == "answer":
        for i, finding in enumerate(reply.findings):
            if finding.paper_id not in known:
                continue
            claims.append(ScientificClaim(
                claim_id=f"baseline-{i}", paper_id=finding.paper_id, statement=finding.statement,
                outcome=finding.outcome, intervention_or_exposure=finding.exposure, direction=finding.direction,
                evidence_passage_ids=[f"{finding.paper_id}-p0"],
            ))
        claims = normalize_claims(claims)  # same name normalization the pipeline applies
        claim_of = {c.paper_id: c.claim_id for c in claims}
    comparisons = [
        {"claim_a_id": claim_of[pair.paper_a], "claim_b_id": claim_of[pair.paper_b],
         "disagreement_type": None if pair.label == "agreement" else pair.label}
        for pair in reply.pairs if pair.paper_a in claim_of and pair.paper_b in claim_of
    ]
    usage = model.usage[-1] if model.usage else {}
    return {
        "report": {
            "claims": [c.model_dump() for c in claims],
            "comparisons": comparisons,
            "clarification_question": (reply.clarification_question or "Please clarify.") if reply.behaviour == "clarify" else None,
        },
        "baseline_behaviour": reply.behaviour,
        "invented_paper_ids": invented,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }
