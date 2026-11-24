import re
from itertools import combinations

from .providers import digest, normalize_doi
from .schemas import ClaimComparison, Comparability, ScientificClaim, VerificationResult

CONTEXT_FIELDS = (
    "outcome",
    "study_system",
    "population_or_material",
    "method",
    "intervention_or_exposure",
    "comparator",
    "duration",
    "effect_size",
    "units",
    "sample_size",
)


def normalize_claims(claims: list[ScientificClaim]) -> list[ScientificClaim]:
    from .domain import canonical, load_domain

    domain = load_domain()
    unique = {}
    for claim in claims:
        claim = claim.model_copy(deep=True)
        for field in CONTEXT_FIELDS:
            value = getattr(claim, field)
            if isinstance(value, str) and value.strip().casefold() in {
                "null",
                "unknown",
                "not reported",
                "n/a",
            }:
                setattr(claim, field, None)
        claim.outcome = canonical(claim.outcome, domain.get("outcome_keywords", {}))
        claim.intervention_or_exposure = canonical(
            claim.intervention_or_exposure, domain.get("exposure_keywords", {})
        )
        claim.missing_fields = [
            field for field in CONTEXT_FIELDS if getattr(claim, field) is None
        ]
        unique[(claim.paper_id, claim.statement.casefold())] = claim
    return list(unique.values())


def compare_value(left, right):
    if left is None or right is None:
        return None
    return str(left).strip().casefold() == str(right).strip().casefold()


def check_comparability(left: ScientificClaim, right: ScientificClaim) -> Comparability:
    differences, missing = [], []
    for field in (
        "study_system",
        "population_or_material",
        "method",
        "intervention_or_exposure",
        "comparator",
        "duration",
        "units",
    ):
        same = compare_value(getattr(left, field), getattr(right, field))
        if same is False:
            differences.append(
                f"{field}: {getattr(left, field)} vs {getattr(right, field)}"
            )
        if same is None:
            missing.append(field)
    if left.conditions != right.conditions and left.conditions and right.conditions:
        differences.append(f"conditions: {left.conditions} vs {right.conditions}")
    return Comparability(
        same_outcome=compare_value(left.outcome, right.outcome),
        comparable_system=compare_value(left.study_system, right.study_system),
        comparable_methods=compare_value(left.method, right.method),
        compatible_units=compare_value(left.units, right.units),
        same_exposure=compare_value(
            left.intervention_or_exposure, right.intervention_or_exposure
        ),
        context_differences=differences,
        missing_context=missing,
    )


def classify_disagreement(
    left: ScientificClaim, right: ScientificClaim
) -> ClaimComparison:
    context = check_comparability(left, right)
    relationship, category = "unclear", "insufficient_evidence"
    notes = (
        ["Missing context: " + ", ".join(context.missing_context)]
        if context.missing_context
        else []
    )
    explanation = (
        "The retrieved evidence lacks critical context for a defensible comparison."
    )
    if (
        context.same_outcome is False
        or context.compatible_units is False
        or context.same_exposure is False
    ):
        relationship, category = "not_comparable", "apparent_disagreement"
        explanation = "These claims concern different outcomes, exposures, or incompatible units; this is not a direct contradiction."
    elif (
        context.same_outcome
        and left.direction == right.direction
        and left.direction not in {"unclear", "mixed"}
    ):
        relationship, category = "agreement", None
        explanation = "The reported directions agree for the normalized outcome; agreement does not establish identical effect sizes or causality."
    elif context.same_outcome and {left.direction, right.direction} == {
        "positive",
        "negative",
    }:
        relationship = "opposition"
        if context.context_differences:
            category = "contextual_disagreement"
            explanation = "Opposing directions occur alongside observed context differences; those differences may explain, but do not prove the cause of, the disagreement."
        elif all(
            value is True
            for value in (
                context.comparable_system,
                context.comparable_methods,
                context.same_exposure,
            )
        ):
            category = "genuine_contradiction"
            explanation = "Opposing directions remain under the reported comparable system, method, and exposure. This is a candidate contradiction, not a scientific verdict."
    elif context.same_outcome and "no_effect" in {left.direction, right.direction}:
        notes.append(
            "A non-significant result is not proof of no effect or of an opposing effect."
        )
        other = ({left.direction, right.direction} - {"no_effect"}) or {"no_effect"}
        if (
            other <= {"positive", "negative"}
            and context.same_exposure is True
            and context.context_differences
        ):
            # Divergent conclusions with known context differences. Never escalated
            # to genuine_contradiction: "no detected effect" is not an opposite effect.
            relationship, category = "divergence", "contextual_disagreement"
            explanation = (
                "One study reports an effect and the other reports no detectable effect, "
                "alongside observed context differences that may explain, but do not prove "
                "the cause of, the divergence."
            )
    elif "no_effect" in {left.direction, right.direction}:
        notes.append(
            "A non-significant result is not proof of no effect or of an opposing effect."
        )
    identifiers = list(
        dict.fromkeys(left.evidence_passage_ids + right.evidence_passage_ids)
    )
    comparison = ClaimComparison(
        comparison_id="comparison-" + digest(left.claim_id + ":" + right.claim_id)[:16],
        claim_a_id=left.claim_id,
        claim_b_id=right.claim_id,
        same_outcome=context.same_outcome,
        comparable_system=context.comparable_system,
        comparable_methods=context.comparable_methods,
        direction_relationship=relationship,
        disagreement_type=category,
        explanation=explanation,
        context_differences=context.context_differences,
        supporting_passage_ids=identifiers,
        uncertainty_notes=notes,
    )
    return comparison


def comparable_pairs(claims: list[ScientificClaim]) -> int:
    return sum(
        left.paper_id != right.paper_id
        and check_comparability(left, right).same_outcome is True
        for left, right in combinations(claims, 2)
    )


def verify_citation(claim, papers, passages, canonical, model=None):
    paper = next((paper for paper in papers if paper.paper_id == claim.paper_id), None)
    selected = {passage.passage_id: passage for passage in passages}
    evidence = [
        selected[identifier]
        for identifier in claim.evidence_passage_ids
        if identifier in selected
    ]
    valid_passages = len(evidence) == len(claim.evidence_passage_ids) and all(
        passage.paper_id == claim.paper_id
        and passage.passage_id in canonical
        and canonical[passage.passage_id].model_dump() == passage.model_dump()
        and passage.content_hash == digest(passage.text)
        for passage in evidence
    )
    source = bool(
        paper
        and paper.source_checked_at
        and paper.source_url
        and re.match(r"^https://[^/]+", paper.source_url)
        and (normalize_doi(paper.doi) or paper.provider_id)
    )
    support, reason = (
        "no",
        "Missing source, foreign passage, corrupted text, or unsupported claim.",
    )
    if paper and source and valid_passages:
        if model:
            judgment = model.supports(claim, evidence)
            support = (
                judgment.support
                if judgment.support in {"yes", "partial", "no", "unclear"}
                else "unclear"
            )
            reason = judgment.reason
        else:
            support, reason = "unclear", "No semantic verifier configured."
    status = (
        "verified"
        if support == "yes" and source and valid_passages
        else (
            "qualified"
            if support == "partial" and source and valid_passages
            else "rejected"
        )
    )
    return VerificationResult(
        claim_id=claim.claim_id,
        paper_exists=paper is not None,
        source_resolves=source,
        source_check=(
            (
                "cached_snapshot"
                if paper and paper.provider == "source_checked_excerpt"
                else "live_provider"
            )
            if source
            else "unverified"
        ),
        passage_exists=valid_passages,
        passage_supports_claim=support,
        status=status,
        reason=reason,
    )


def assess_evidence_quality(papers, claims, passages) -> list[str]:
    notes = [
        "Evidence navigation only: not an exhaustive review, meta-analysis, scientific verdict, or clinical recommendation.",
        "Source validation confirms cached/provider identity, not a fresh HTTP/DOI resolution or independent scientific truth.",
    ]
    if any(
        paper.paper_id
        not in {
            passage.paper_id
            for passage in passages
            if passage.source_type == "full_text"
        }
        for paper in papers
    ):
        notes.append(
            "Some included studies have only short abstract-level excerpts; methods and results may be missing."
        )
    missing = sorted({field for claim in claims for field in claim.missing_fields})
    if missing:
        notes.append(
            "Unreported or unavailable fields remain unknown: "
            + ", ".join(missing)
            + "."
        )
    return notes
