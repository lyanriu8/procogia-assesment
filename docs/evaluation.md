# Actual model evaluation

`python -m contradiction_lab evaluate` executes eight scenarios in both workflows, followed by a compact/evidence-rich comparison. All inference runs through Ollama. Source documents contain no extraction annotations.

Scenarios cover productivity, ambiguity, an unrelated question, a one-paper date filter, injected unsupported text, an invalid citation, provider outage, and synonym discovery. Fault injections are explicitly marked in raw runs and are never part of public source documents.

The harness records expected and observed report status, clarification, verified-claim minimums, fault rejection, comparison membership, adaptive bounds, model calls, actual input/output token counts, latency, errors, and routing. Every raw run is saved. Failed checks remain failures; they are not removed to improve the summary.

The two context configurations use top-K 4 with abstract preference and top-K 8 with methods/results preference. Both K and ranking preferences change, so differences cannot be attributed solely to K. Compare retrieved evidence, verified findings, tokens, and timing. Run `scripts/compare_settings.py` for a separate K-only change and the two requested routing-setting changes.

These are repeatable behavioral expectations, not human-reviewed scientific labels. The verifier is the same model as the extractor. Structural exclusion of unverified claims is not an independent hallucination metric. Do not claim extraction F1 based on exact generated wording, or scientific classification accuracy based on these six papers. Add domain reviewers, real opposing study pairs, and held-out data before making those claims.

`pytest` uses explicit test mocks for model calls while running real LangGraph and Chroma. Passing tests does not substitute for Ollama integration runs. Historical replay artifacts are archived separately and are not current results.
