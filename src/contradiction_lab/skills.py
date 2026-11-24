import re
from itertools import combinations

from .llm import ModelError
from .providers import digest, normalize_doi
from .schemas import ClaimComparison, Comparability, ScientificClaim, SearchPlan, VerificationResult


CONTEXT_FIELDS = ("outcome", "study_system", "population_or_material", "method", "intervention_or_exposure", "comparator", "duration", "effect_size", "units", "sample_size")


def plan_research(query: str) -> SearchPlan:
    meaningful = re.findall(r"[A-Za-z]{3,}", query)
    ambiguous = len(meaningful) < 3 or query.strip().lower() in {"does it work?", "compare these papers", "what about this?"}
    return SearchPlan(query=query, search_terms=[query], interpreted_scope=query.strip(), needs_clarification=ambiguous,
                      clarification_question="Which exposure or intervention, study system, and outcome should be compared?" if ambiguous else None)


def normalize_claims(claims: list[ScientificClaim]) -> list[ScientificClaim]:
    aliases = {"aboveground biomass": "productivity", "ecosystem productivity": "productivity", "primary productivity": "productivity"}
    unique = {}
    for claim in claims:
        claim = claim.model_copy(deep=True)
        if claim.outcome:
            claim.outcome = aliases.get(claim.outcome.strip().lower(), claim.outcome.strip().lower())
        claim.missing_fields = [field for field in CONTEXT_FIELDS if getattr(claim, field) is None]
        unique[(claim.paper_id, claim.statement.casefold())] = claim
    return list(unique.values())


def compare_value(left, right):
    if left is None or right is None:
        return None
    return str(left).strip().casefold() == str(right).strip().casefold()


def check_comparability(left: ScientificClaim, right: ScientificClaim) -> Comparability:
    differences, missing = [], []
    for field in ("study_system", "population_or_material", "method", "intervention_or_exposure", "comparator", "duration", "units"):
        same = compare_value(getattr(left, field), getattr(right, field))
        if same is False:
            differences.append(f"{field}: {getattr(left, field)} vs {getattr(right, field)}")
        if same is None:
            missing.append(field)
    if left.conditions != right.conditions and left.conditions and right.conditions:
        differences.append(f"conditions: {left.conditions} vs {right.conditions}")
    return Comparability(
        same_outcome=compare_value(left.outcome, right.outcome),
        comparable_system=compare_value(left.study_system, right.study_system),
        comparable_methods=compare_value(left.method, right.method),
        compatible_units=compare_value(left.units, right.units),
        same_exposure=compare_value(left.intervention_or_exposure, right.intervention_or_exposure),
        context_differences=differences, missing_context=missing,
    )


def classify_disagreement(left: ScientificClaim, right: ScientificClaim, model=None, passages=None) -> ClaimComparison:
    context = check_comparability(left, right)
    relationship, category = "unclear", "insufficient_evidence"
    notes = ["Missing context: " + ", ".join(context.missing_context)] if context.missing_context else []
    explanation = "The retrieved evidence lacks critical context for a defensible comparison."
    if context.same_outcome is False or context.compatible_units is False or context.same_exposure is False:
        relationship, category = "not_comparable", "apparent_disagreement"
        explanation = "These claims concern different outcomes, exposures, or incompatible units; this is not a direct contradiction."
    elif context.same_outcome and left.direction == right.direction and left.direction not in {"unclear", "mixed"}:
        relationship, category = "agreement", None
        explanation = "The reported directions agree for the normalized outcome; agreement does not establish identical effect sizes or causality."
    elif context.same_outcome and {left.direction, right.direction} == {"positive", "negative"}:
        relationship = "opposition"
        if context.context_differences:
            category = "contextual_disagreement"
            explanation = "Opposing directions occur alongside observed context differences; those differences may explain, but do not prove the cause of, the disagreement."
        elif all(value is True for value in (context.comparable_system, context.comparable_methods, context.same_exposure)):
            category = "genuine_contradiction"
            explanation = "Opposing directions remain under the reported comparable system, method, and exposure. This is a candidate contradiction, not a scientific verdict."
    elif "no_effect" in {left.direction, right.direction}:
        notes.append("A non-significant result is not proof of no effect or of an opposing effect.")
    identifiers = list(dict.fromkeys(left.evidence_passage_ids + right.evidence_passage_ids))
    comparison = ClaimComparison(
        comparison_id="comparison-" + digest(left.claim_id + ":" + right.claim_id)[:16],
        claim_a_id=left.claim_id, claim_b_id=right.claim_id, same_outcome=context.same_outcome,
        comparable_system=context.comparable_system, comparable_methods=context.comparable_methods,
        direction_relationship=relationship, disagreement_type=category, explanation=explanation,
        context_differences=context.context_differences, supporting_passage_ids=identifiers, uncertainty_notes=notes,
    )
    if model:
        semantic = model.structured(ClaimComparison,
                                    "Explain this pair using only the source passages and deterministic checks. Do not strengthen category or change IDs. Explain context differences as possible, not proven causes.",
                                    {"claims": [left.model_dump(), right.model_dump()], "constraints": comparison.model_dump(),
                                     "passages": [passage.model_dump() for passage in passages or [] if passage.passage_id in identifiers]})
        if semantic.disagreement_type == "insufficient_evidence" and category != "insufficient_evidence":
            comparison.disagreement_type = "insufficient_evidence"
            comparison.direction_relationship = "unclear"
            comparison.explanation = "The semantic reviewer found insufficient support for the deterministic candidate comparison."
        comparison.uncertainty_notes.append("Model interpretation was constrained by deterministic checks; free-form model explanations are excluded from the final report to avoid unverified scientific assertions.")
    return comparison


def comparable_pairs(claims: list[ScientificClaim]) -> int:
    return sum(left.paper_id != right.paper_id and check_comparability(left, right).same_outcome is True
               for left, right in combinations(claims, 2))


def verify_citation(claim, papers, passages, canonical, fixture=None, model=None):
    paper = next((paper for paper in papers if paper.paper_id == claim.paper_id), None)
    selected = {passage.passage_id: passage for passage in passages}
    evidence = [selected[identifier] for identifier in claim.evidence_passage_ids if identifier in selected]
    valid_passages = len(evidence) == len(claim.evidence_passage_ids) and all(
        passage.paper_id == claim.paper_id and passage.passage_id in canonical
        and canonical[passage.passage_id].model_dump() == passage.model_dump()
        and passage.content_hash == digest(passage.text) for passage in evidence)
    source = bool(paper and paper.source_checked_at and paper.source_url and re.match(r"^https://[^/]+", paper.source_url)
                  and (normalize_doi(paper.doi) or paper.provider_id))
    support, reason = "no", "Missing source, foreign passage, corrupted text, or unsupported claim."
    if paper and source and valid_passages:
        if fixture:
            expected = fixture.extract(paper, evidence)
            compared_fields = [field for field in ScientificClaim.model_fields if field not in {"claim_id", "missing_fields", "extraction_confidence"}]
            supported = any(all(getattr(claim, field) == getattr(candidate, field) for field in compared_fields) for candidate in normalize_claims(expected))
            support = "yes" if supported else "no"
            reason = "Matches source-checked extraction replay and intact passages; not independent human entailment review." if supported else "Claim or context differs from the cached extraction; rejected."
        elif model:
            judgment = model.supports(claim, evidence)
            support = judgment.support if judgment.support in {"yes", "partial", "no", "unclear"} else "unclear"
            reason = judgment.reason
        else:
            support, reason = "unclear", "No semantic verifier configured."
    status = "verified" if support == "yes" and source and valid_passages else "qualified" if support == "partial" and source and valid_passages else "rejected"
    return VerificationResult(
        claim_id=claim.claim_id, paper_exists=paper is not None, source_resolves=source,
        source_check=("cached_snapshot" if paper and paper.provider == "source_checked_excerpt" else "live_provider") if source else "unverified",
        passage_exists=valid_passages, passage_supports_claim=support, status=status, reason=reason,
    )


def assess_evidence_quality(papers, claims, passages) -> list[str]:
    notes = ["Evidence navigation only: not an exhaustive review, meta-analysis, scientific verdict, or clinical recommendation.",
             "Source validation confirms cached/provider identity, not a fresh HTTP/DOI resolution or independent scientific truth."]
    if any(paper.paper_id not in {passage.paper_id for passage in passages if passage.source_type == "full_text"} for paper in papers):
        notes.append("Some included studies have only short abstract-level excerpts; methods and results may be missing.")
    missing = sorted({field for claim in claims for field in claim.missing_fields})
    if missing:
        notes.append("Unreported or unavailable fields remain unknown: " + ", ".join(missing) + ".")
    return notes
