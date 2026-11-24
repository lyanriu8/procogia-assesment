from contradiction_lab.schemas import ComparisonReport
from contradiction_lab.ai.research.skills import assess_evidence_quality


def build_comparison_report(state) -> ComparisonReport:
    from contradiction_lab.schemas import Paper, EvidencePassage, ScientificClaim, ClaimComparison, VerificationResult

    papers = [Paper.model_validate(value) for value in state["included_papers"]]
    passages = [EvidencePassage.model_validate(value) for value in state["retrieved_passages"]]
    results = [VerificationResult.model_validate(value) for value in state["verification_results"]]
    verified_ids = {result.claim_id for result in results if result.status == "verified"}
    claims = [ScientificClaim.model_validate(value) for value in state["claims"] if value["claim_id"] in verified_ids]
    comparisons = [ClaimComparison.model_validate(value) for value in state["comparisons"]
                   if value["claim_a_id"] in verified_ids and value["claim_b_id"] in verified_ids]
    usable = [comparison for comparison in comparisons if comparison.direction_relationship in {"agreement", "opposition", "divergence"}
              and comparison.disagreement_type != "insufficient_evidence"]
    thresholds_met = len(claims) >= state["settings"]["min_claims"] and len(usable) >= state["settings"]["min_comparable_pairs"]
    status = "evidence_found" if thresholds_met else "limited_evidence" if claims else "insufficient_evidence"
    if state["errors"] and status == "evidence_found":
        status = "limited_evidence"
    limits = assess_evidence_quality(papers, claims, passages) + state["missing_evidence"]
    limits.extend(f"{error['kind']}: {error['message']}" for error in state["errors"])
    if any(result.status != "verified" for result in results):
        limits.append("Qualified or rejected claims were excluded from synthesis; inspect verification results for reasons.")
    cited_passage_ids = {identifier for claim in claims for identifier in claim.evidence_passage_ids}
    cited_paper_ids = {claim.paper_id for claim in claims}
    agreements = sum(comparison.direction_relationship == "agreement" for comparison in comparisons)
    disagreements = sum(comparison.disagreement_type in {"genuine_contradiction", "contextual_disagreement", "apparent_disagreement"} for comparison in comparisons)
    unresolved = [] if thresholds_met else ["Not enough verified comparable findings for the configured reporting threshold. Broader retrieval and human review are needed."]
    return ComparisonReport(
        query=state["query"], interpreted_scope=state["search_plan"]["interpreted_scope"], workflow_mode=state["workflow_mode"],
        papers_considered=len(state["candidate_papers"]), papers_included=len(cited_paper_ids), claims_extracted=len(state["claims"]),
        claims=claims, comparisons=comparisons, verification_results=results,
        papers=[paper for paper in papers if paper.paper_id in cited_paper_ids],
        passages=[passage for passage in passages if passage.passage_id in cited_passage_ids],
        agreement_summary=f"{agreements} verified claim pair(s) have matching reported directions. Inspect context before inferring a consensus.",
        disagreement_summary=f"{disagreements} pair(s) show potential or apparent disagreement. No study is selected as a winner.",
        evidence_limitations=list(dict.fromkeys(limits)), unresolved_questions=unresolved,
        citations=sorted(cited_passage_ids), overall_status=status,
        clarification_question=(
            state["search_plan"].get("clarification_question")
            or (
                "Which exposure and which outcome do you want to compare?"
                if state["search_plan"].get("needs_clarification")
                else None
            )
        ),
        suggested_questions=(
            state["search_plan"].get("suggested_questions", [])[:3]
            if state["search_plan"].get("needs_clarification")
            else []
        ),
    )


def markdown_report(report: ComparisonReport) -> str:
    def cell(value):
        return str(value if value is not None else "unknown").replace("|", "\\|").replace("\n", " ")

    papers = {paper.paper_id: paper for paper in report.papers}
    lines = [f"# Contradiction Lab: {report.overall_status}", "", report.query, "", report.agreement_summary, report.disagreement_summary, "",
             "| Paper | Year | System | Method | Outcome | Finding | Direction | Passages |", "|---|---|---|---|---|---|---|---|"]
    for claim in report.claims:
        paper = papers[claim.paper_id]
        lines.append("| " + " | ".join(map(cell, [paper.title, paper.publication_year, claim.study_system, claim.method, claim.outcome,
                                                     claim.statement, claim.direction, ", ".join(claim.evidence_passage_ids)])) + " |")
    lines.extend(["", "## Comparisons"])
    for comparison in report.comparisons:
        lines.extend([f"- {comparison.comparison_id}: {comparison.disagreement_type or 'agreement'} — {comparison.explanation}",
                      f"  Evidence: {', '.join(comparison.supporting_passage_ids)}"])
    lines.extend(["", "## Limitations", *["- " + limitation for limitation in report.evidence_limitations],
                  "", "## Unresolved", *["- " + question for question in report.unresolved_questions], "", "## Sources"])
    for passage in report.passages:
        lines.append(f"- {passage.passage_id} ({passage.source_type}; {passage.section}): {passage.source_url}\n  > {passage.text}")
    if report.clarification_question:
        lines.extend(["", "## Clarification", report.clarification_question])
    return "\n".join(lines) + "\n"
