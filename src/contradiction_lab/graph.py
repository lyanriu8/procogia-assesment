import json
import logging
import time
import uuid
from itertools import combinations
from typing import TypedDict

from .config import Settings
from .corpus import PublicCorpus
from .llm import ModelError, OllamaModel
from .providers import EuropePMC, HTTPClient, OpenAlex, ProviderError, deduplicate, digest
from .reporting import build_comparison_report
from .retrieval import OllamaEmbedding, VectorIndex, chunk_text, tokens
from .schemas import EvidencePassage, Paper, ResearchRequest, ScientificClaim, TraceEvent, utcnow
from .skills import check_comparability, classify_disagreement, comparable_pairs, normalize_claims, plan_research, verify_citation
from .storage import Store


logger = logging.getLogger(__name__)


class ResearchState(TypedDict, total=False):
    run_id: str
    query: str
    workflow_mode: str
    settings: dict
    request: dict
    search_plan: dict
    search_query: str
    retrieval_query: str
    candidate_papers: list[dict]
    included_papers: list[dict]
    all_passages: list[dict]
    retrieved_passages: list[dict]
    claims: list[dict]
    study_contexts: list[dict]
    comparisons: list[dict]
    verification_results: list[dict]
    missing_evidence: list[str]
    routing_reason: str | None
    next_route: str
    iteration_count: int
    attempted_actions: list[str]
    errors: list[dict]
    trace: list[dict]
    final_report: dict | None
    fault: str | None
    paper_subset: list[str] | None


STATIC_NODES = ["plan_research", "retrieve_papers", "retrieve_passages", "extract_claims", "analyze_context", "compare_claims", "verify_evidence", "build_report"]
ADAPTIVE_ACTIONS = ["broaden_search", "retrieve_full_text", "refine_comparison"]


def route_after_sufficiency(state: ResearchState) -> tuple[str, str]:
    settings = state["settings"]
    claims = [ScientificClaim.model_validate(value) for value in state["claims"]]
    attempted = state["attempted_actions"]
    if state["search_plan"].get("needs_clarification"):
        return "verify_with_limitations", "Question needs clarification; no fabricated search scope."
    if any(error["kind"] == "provider_error" for error in state["errors"]) and not claims:
        return "verify_with_limitations", "Discovery failed; API failure is not evidence of absence."
    enough = len(claims) >= settings["min_claims"] and comparable_pairs(claims) >= settings["min_comparable_pairs"]
    missing_full_text = any(paper["full_text_available"] and any(claim.paper_id == paper["paper_id"] and claim.method is None for claim in claims)
                            for paper in state["included_papers"])
    if enough and (not missing_full_text or "retrieve_full_text" in attempted):
        return "analyze_context", "Enough extracted comparable findings; verification still required."
    if state["iteration_count"] >= settings["max_iterations"]:
        return "verify_with_limitations", "Adaptive iteration budget exhausted."
    if (not state["included_papers"] or len(claims) < settings["min_claims"]) and "broaden_search" not in attempted:
        return "broaden_search", "Too few relevant papers or findings; broaden once within the shared budget."
    if missing_full_text and "retrieve_full_text" not in attempted:
        return "retrieve_full_text", "Methods/results are missing; try permitted accessible full text once."
    if claims and "refine_comparison" not in attempted:
        return "refine_comparison", "No sufficient comparable claim pairs; focus retrieval on a reported outcome."
    return "verify_with_limitations", "No useful untried adaptation remains; stop with limitations."


def compile_graph(nodes: dict, mode: str, runtime: str):
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        raise RuntimeError("LangGraph is required. Install the project dependencies.") from None
    builder = StateGraph(ResearchState)
    names = STATIC_NODES if mode == "static" else STATIC_NODES + ADAPTIVE_ACTIONS + ["assess_sufficiency", "verify_with_limitations"]
    for name in names:
        builder.add_node(name, nodes[name])
    builder.add_edge(START, "plan_research")
    for left, right in zip(STATIC_NODES, STATIC_NODES[1:]):
        builder.add_edge(left, "assess_sufficiency" if mode == "dynamic" and left == "extract_claims" else right)
    builder.add_edge("build_report", END)
    if mode == "dynamic":
        routes = ADAPTIVE_ACTIONS + ["analyze_context", "verify_with_limitations"]
        builder.add_conditional_edges("assess_sufficiency", lambda state: state["next_route"], {route: route for route in routes})
        builder.add_edge("broaden_search", "retrieve_papers")
        builder.add_edge("retrieve_full_text", "retrieve_passages")
        builder.add_edge("refine_comparison", "retrieve_passages")
        builder.add_edge("verify_with_limitations", "analyze_context")
    return builder.compile()


class ResearchEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.store = Store(self.settings.data_dir / "lab.sqlite3")

    def run(self, request: ResearchRequest, *, fault=None, paper_subset=None, run_id=None) -> dict:
        overrides = {key: getattr(request, key) for key in ("max_papers", "top_k", "max_iterations", "context_config") if getattr(request, key) is not None}
        if request.context_config == "compact" and request.top_k is None:
            overrides["top_k"] = 4
        settings = Settings.model_validate({**self.settings.model_dump(), **overrides})
        run_id = run_id or uuid.uuid4().hex
        corpus = PublicCorpus() if settings.source == "corpus" else None
        model = OllamaModel(settings)
        client = HTTPClient(settings, self.store)
        embedding = OllamaEmbedding(settings.embedding_model)
        index = VectorIndex(self.store, run_id, embedding, settings.vector_backend)
        worker = Nodes(settings, self.store, corpus, model, client, index)
        state: ResearchState = {
            "run_id": run_id, "query": request.query.strip(), "workflow_mode": request.workflow,
            "settings": settings.model_dump(mode="json"), "request": request.model_dump(mode="json"),
            "search_plan": {}, "search_query": request.query.strip(), "retrieval_query": request.query.strip(), "candidate_papers": [], "included_papers": [],
            "all_passages": [], "retrieved_passages": [], "claims": [], "study_contexts": [], "comparisons": [],
            "verification_results": [], "missing_evidence": [], "routing_reason": None, "next_route": "",
            "iteration_count": 0, "attempted_actions": [], "errors": [], "trace": [], "final_report": None,
            "fault": fault, "paper_subset": paper_subset,
        }
        nodes = {name: worker.instrument(name) for name in STATIC_NODES + ADAPTIVE_ACTIONS + ["assess_sufficiency", "verify_with_limitations"]}
        graph = compile_graph(nodes, request.workflow, settings.runtime)
        final = graph.invoke(state, {"recursion_limit": 20 + settings.max_iterations * 8})
        result = {"run_id": run_id, "status": final["final_report"]["overall_status"], "report": final["final_report"],
                  "trace": final["trace"], "errors": final["errors"], "config": settings.model_dump(mode="json"),
                  "embedding": embedding.name, "model": model.model,
                  "prompt_version": "grounded-v1", "source_mode": settings.source,
                  "request": request.model_dump(mode="json"), "retrieved_passage_ids": [passage["passage_id"] for passage in final["retrieved_passages"]],
                  "extracted_claims": final["claims"], "benchmark_fault": fault,
                  "implementation_version": "0.1.0", "corpus_version": corpus.raw["version"] if corpus else None,
                  "config_hash": digest(settings.model_dump_json())}
        self.store.put("runs", run_id, result)
        return result


class Nodes:
    def __init__(self, settings, store, corpus, model, client, index):
        self.settings, self.store, self.corpus, self.model, self.client, self.index = settings, store, corpus, model, client, index

    def instrument(self, name):
        def execute(original):
            state = dict(original)
            state["errors"] = list(original["errors"])
            state["missing_evidence"] = list(original["missing_evidence"])
            started, clock = utcnow(), time.perf_counter()
            self.store.put("runs", state["run_id"], {"run_id":state["run_id"],"status":"running","current_node":name,"trace":state["trace"],"query":state["query"]})
            usage_start = len(self.model.usage) if self.model else 0
            retries_start = self.client.retries
            try:
                updates = getattr(self, name)(state) or {}
                state.update(updates)
            except (ProviderError, ModelError) as error:
                state["errors"].append({"kind": "provider_error" if isinstance(error, ProviderError) else "model_error", "node": name, "message": str(error)})
                if name == "plan_research":
                    state["search_plan"] = {"interpreted_scope": state["query"], "needs_clarification": False}
                    state["missing_evidence"].append("Planning model failed; no answer was substituted.")
                if name == "assess_sufficiency":
                    state["next_route"] = "verify_with_limitations"
                    state["routing_reason"] = "Routing model unavailable; stopping safely."
                if name == "extract_claims":
                    state["claims"] = []
            usage = self.model.usage[usage_start:] if self.model else []
            event = TraceEvent(
                node=name, started_at=started, ended_at=utcnow(), latency_ms=round((time.perf_counter() - clock) * 1000, 3),
                papers=len(state["included_papers"]), passages=len(state["retrieved_passages"]), claims=len(state["claims"]),
                iteration=state["iteration_count"], route=state["next_route"] if name == "assess_sufficiency" else None,
                reason=state["routing_reason"] if name in {"assess_sufficiency", "verify_with_limitations"} else None,
                model=self.model.model,
                input_tokens=sum(item["input_tokens"] for item in usage), output_tokens=sum(item["output_tokens"] for item in usage),
                token_measurement="provider_reported" if usage else "not_applicable (no LLM call)",
                retries=self.client.retries - retries_start + sum(item["repair"] > 0 for item in usage),
                errors=[error["message"] for error in state["errors"][len(original["errors"]):]],
            )
            state["trace"] = original["trace"] + [event.model_dump(mode="json")]
            self.store.put("runs",state["run_id"],{"run_id":state["run_id"],"status":"running","current_node":name,"trace":state["trace"],"query":state["query"]})
            logger.info("graph_node %s", json.dumps({"run_id": state["run_id"], **event.model_dump(mode="json")}))
            return state
        return execute

    def plan_research(self, state):
        plan = self.model.plan(state["query"])
        return {"search_plan": plan.model_dump(), "search_query": plan.search_terms[0] if plan.search_terms else state["query"]}

    def retrieve_papers(self, state):
        if state["search_plan"].get("needs_clarification") or any(e["kind"] == "model_error" for e in state["errors"]):
            return {}
        if state["fault"] == "provider_error":
            raise ProviderError("Injected benchmark provider timeout; no results cannot be inferred")
        request = state["request"]
        if self.corpus:
            from datetime import date

            papers = self.corpus.search(state["search_query"], self.settings.max_papers, self.index.embedding,
                                        date.fromisoformat(request["date_from"]) if request["date_from"] else None,
                                        date.fromisoformat(request["date_to"]) if request["date_to"] else None, self.settings.discovery_min_similarity)
            if state["paper_subset"] is not None:
                papers = [paper for paper in papers if paper.paper_id in state["paper_subset"]]
        else:
            papers = []
            providers = {"openalex": OpenAlex(self.client), "europepmc": EuropePMC(self.client)}
            for source in request["sources"]:
                try:
                    papers += providers[source].search(state["search_query"], self.settings.max_papers, request["date_from"], request["date_to"])
                except ProviderError as error:
                    state["errors"].append({"kind": "provider_error", "node": "retrieve_papers", "message": f"{source}: {error}"})
        previous = [Paper.model_validate(value) for value in state["candidate_papers"]]
        papers = deduplicate(previous + papers)[:self.settings.max_papers]
        for paper in papers:
            self.store.save_paper(paper)
        passages = {value["passage_id"]: value for value in state["all_passages"]}
        for paper in papers:
            if self.corpus:
                for passage in self.corpus.passages:
                    if passage.paper_id == paper.paper_id and (passage.source_type != "full_text" or state["workflow_mode"] == "static" or not paper.full_text_available):
                        passages[passage.passage_id] = passage.model_dump()
            elif paper.abstract:
                for passage in chunk_text(paper, paper.abstract, "Abstract", "abstract", self.settings.chunk_size_tokens, self.settings.chunk_overlap_tokens):
                    passages[passage.passage_id] = passage.model_dump()
            if not self.corpus and state["workflow_mode"] == "static" and paper.full_text_available:
                try:
                    _, extra = self.fetch_full_text(paper)
                    for passage in extra:
                        passages[passage.passage_id] = passage.model_dump()
                    self.store.save_paper(paper)
                except ProviderError as error:
                    state["errors"].append({"kind": "provider_error", "node": "retrieve_papers", "message": str(error)})
        if not papers:
            state["missing_evidence"].append("no_results: the selected corpus returned no relevant papers for this scope.")
        return {"candidate_papers": [paper.model_dump(mode="json") for paper in papers],
                "included_papers": [paper.model_dump(mode="json") for paper in papers], "all_passages": list(passages.values())}

    def retrieve_passages(self, state):
        passages = [EvidencePassage.model_validate(value) for value in state["all_passages"]]
        self.index.upsert(passages)
        selected = self.index.search(state["retrieval_query"], [paper["paper_id"] for paper in state["included_papers"]],
                                     self.settings.top_k, self.settings.context_config, self.settings.context_tokens)
        return {"retrieved_passages": [passage.model_dump() for passage in selected]}

    def extract_claims(self, state):
        passages = [EvidencePassage.model_validate(value) for value in state["retrieved_passages"]]
        claims = []
        for record in state["included_papers"]:
            paper = Paper.model_validate(record)
            evidence = [passage for passage in passages if passage.paper_id == paper.paper_id and passage.source_type != "metadata"]
            if not evidence:
                continue
            extracted = self.model.extract(paper, evidence, state["query"])
            allowed = {passage.passage_id for passage in evidence}
            for claim in extracted[:self.settings.max_claims_per_paper]:
                if claim.paper_id == paper.paper_id and set(claim.evidence_passage_ids) <= allowed:
                    if self.model:
                        claim.claim_id = "claim-" + digest(paper.paper_id + ":" + claim.statement)[:20]
                    claims.append(claim)
                else:
                    state["errors"].append({"kind": "extraction_error", "node": "extract_claims", "message": "Foreign paper or unknown passage IDs rejected."})
        claims = normalize_claims(claims)
        if claims and state["fault"] == "unsupported_claim":
            claims[0].statement = "This proves every ecosystem doubles its productivity."
        if claims and state["fault"] == "invalid_citation":
            claims[0].evidence_passage_ids = ["missing-passage"]
        return {"claims": [claim.model_dump() for claim in claims]}

    def assess_sufficiency(self, state):
        route, reason = route_after_sufficiency(state)
        if route not in {"verify_with_limitations", "analyze_context"}:
            from .schemas import RouteDecision
            allowed = ["verify_with_limitations"]
            if "broaden_search" not in state["attempted_actions"]:
                allowed.append("broaden_search")
            if any(p["full_text_available"] for p in state["included_papers"]) and "retrieve_full_text" not in state["attempted_actions"]:
                allowed.append("retrieve_full_text")
            if state["claims"] and "refine_comparison" not in state["attempted_actions"]:
                allowed.append("refine_comparison")
            decision = self.model.structured(RouteDecision,
                "Choose a useful next research action from allowed_actions. Prefer suggested_action when appropriate. Never repeat an attempted action. Stop when none can help. Explain briefly.",
                {"question":state["query"], "claims":state["claims"], "allowed_actions":allowed, "suggested_action":route, "missing_evidence":reason})
            if decision.action in allowed:
                route, reason = decision.action, decision.reason
        return {"next_route": route, "routing_reason": reason}

    def broaden_search(self, state):
        plan = self.model.structured(__import__("contradiction_lab.schemas", fromlist=["SearchPlan"]).SearchPlan,
            "Broaden the original scholarly search using simpler synonyms. Preserve the intervention and outcome; do not change the scientific question.", {"query":state["query"], "previous_search":state["search_query"]})
        broadened = plan.search_terms[0] if plan.search_terms else state["query"]
        return {"search_query": broadened, "iteration_count": state["iteration_count"] + 1,
                "attempted_actions": state["attempted_actions"] + ["broaden_search"]}

    def retrieve_full_text(self, state):
        state["iteration_count"] += 1
        state["attempted_actions"] = state["attempted_actions"] + ["retrieve_full_text"]
        passages = {value["passage_id"]: value for value in state["all_passages"]}
        found = False
        papers = [Paper.model_validate(value) for value in state["included_papers"]]
        for paper in papers:
            if not paper.full_text_available:
                continue
            paper, extra = self.fetch_full_text(paper)
            for passage in extra:
                passages[passage.passage_id] = passage.model_dump()
                found = True
        if not found:
            state["missing_evidence"].append("no_full_text: no additional text with a permitted license was available.")
        return {"all_passages": list(passages.values()), "included_papers": [paper.model_dump(mode="json") for paper in papers],
                "iteration_count": state["iteration_count"], "attempted_actions": state["attempted_actions"]}

    def fetch_full_text(self, paper):
        if self.corpus:
            return paper, [passage for passage in self.corpus.passages if passage.paper_id == paper.paper_id and passage.source_type == "full_text"]
        provider = EuropePMC(self.client)
        paper = provider.enrich(paper)
        self.store.save_paper(paper)
        extra = [passage for section, text in provider.full_text(paper)
                 for passage in chunk_text(paper, text, section, "full_text", self.settings.chunk_size_tokens, self.settings.chunk_overlap_tokens)]
        return paper, extra

    def refine_comparison(self, state):
        outcomes = [claim["outcome"] for claim in state["claims"] if claim["outcome"]]
        focus = outcomes[0] if outcomes else state["query"]
        return {"retrieval_query": f"{focus} {state['query']}", "iteration_count": state["iteration_count"] + 1,
                "attempted_actions": state["attempted_actions"] + ["refine_comparison"]}

    def verify_with_limitations(self, state):
        state["missing_evidence"].append(state["routing_reason"] or "Evidence remains insufficient.")

    def analyze_context(self, state):
        claims = [ScientificClaim.model_validate(value) for value in state["claims"]]
        return {"study_contexts": [{"claim_a_id": left.claim_id, "claim_b_id": right.claim_id,
                                    **check_comparability(left, right).model_dump()}
                                   for left, right in combinations(claims, 2) if left.paper_id != right.paper_id]}

    def compare_claims(self, state):
        claims = [ScientificClaim.model_validate(value) for value in state["claims"]]
        passages = [EvidencePassage.model_validate(value) for value in state["retrieved_passages"]]
        pairs = [(left, right) for left, right in combinations(claims, 2) if left.paper_id != right.paper_id]
        if len(pairs) > self.settings.max_comparisons:
            state["missing_evidence"].append("Pair comparison budget reached; not all claim pairs were analyzed.")
        from .schemas import PairJudgments
        selected = pairs[:self.settings.max_comparisons]
        comparisons = []
        if selected:
            judgments = self.model.structured(PairJudgments,
                "Compare each pair IN ORDER. Return exactly one judgment per pair. Use agreement when same-outcome effects point in the same direction. Different outcomes/exposures are apparent_disagreement and not_comparable. Opposing effects with known differing context are contextual_disagreement; missing critical context means insufficient_evidence. Genuine contradiction requires known matching critical context. Explain briefly using only supplied evidence. Never claim a context difference proves causation.",
                {"pairs":[{"left":a.model_dump(exclude_none=True,exclude_defaults=True),"right":b.model_dump(exclude_none=True,exclude_defaults=True)} for a,b in selected]})
            if len(judgments.judgments) != len(selected):
                raise ModelError("Comparison model returned wrong number of pair judgments")
            for (left,right), judgment in zip(selected,judgments.judgments):
                comparison = classify_disagreement(left,right)
                # Hard scientific constraints cap the model's interpretation.
                if comparison.disagreement_type not in {"apparent_disagreement", "insufficient_evidence"}:
                    if judgment.disagreement_type == "insufficient_evidence" or judgment.direction_relationship == "unclear":
                        comparison.disagreement_type = "insufficient_evidence"
                        comparison.direction_relationship = "unclear"
                comparison.uncertainty_notes.append("LLM assessment: " + judgment.explanation)
                comparisons.append(comparison.model_dump())
        return {"comparisons": comparisons}

    def verify_evidence(self, state):
        papers = [Paper.model_validate(value) for value in state["included_papers"]]
        passages = [EvidencePassage.model_validate(value) for value in state["retrieved_passages"]]
        canonical = {value["passage_id"]: EvidencePassage.model_validate(value) for value in state["all_passages"]}
        results = []
        for value in state["claims"]:
            claim = ScientificClaim.model_validate(value)
            try:
                result = verify_citation(claim, papers, passages, canonical, self.model)
            except ModelError as error:
                state["errors"].append({"kind": "model_error", "node": "verify_evidence", "message": str(error)})
                result = verify_citation(claim, papers, passages, canonical)
            results.append(result.model_dump())
        return {"verification_results": results}

    def build_report(self, state):
        return {"final_report": build_comparison_report(state).model_dump(mode="json")}
