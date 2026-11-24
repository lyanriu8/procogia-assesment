# Actual model evaluation

`python -m contradiction_lab evaluate` executes eight scenarios in both workflows, followed by a compact/evidence-rich comparison. All inference runs through Ollama. Source documents contain no extraction annotations.

Scenarios cover productivity, ambiguity, an unrelated question, a one-paper date filter, injected unsupported text, an invalid citation, provider outage, and synonym discovery. Fault injections are explicitly marked in raw runs and are never part of public source documents.

The harness records expected and observed report status, clarification, verified-claim minimums, fault rejection, comparison membership, adaptive bounds, model calls, actual input/output token counts, latency, errors, and routing. Every raw run is saved. Failed checks remain failures; they are not removed to improve the summary.

The two context configurations use top-K 4 with abstract preference and top-K 8 with methods/results preference. Both K and ranking preferences change, so differences cannot be attributed solely to K. Compare retrieved evidence, verified findings, tokens, and timing. Run `scripts/compare_settings.py` for a separate K-only change and the two requested routing-setting changes.

These are repeatable behavioral expectations, not human-reviewed scientific labels. The verifier is the same model as the extractor. Structural exclusion of unverified claims is not an independent hallucination metric. Do not claim extraction F1 based on exact generated wording, or scientific classification accuracy based on these six papers. Add domain reviewers, real opposing study pairs, and held-out data before making those claims.

`pytest` uses explicit test mocks for model calls while running real LangGraph and Chroma. Passing tests does not substitute for Ollama integration runs. Historical replay artifacts are archived separately and are not current results.

## Recorded presentation validation

The saved eight-scenario real-model sample passed **7/8 strict behavioral checks**. Static and dynamic success, ambiguity, uncertainty, invalid citation rejection, missing-information adaptation, and context measurements completed. The unsupported universal statement was judged partial/qualified rather than rejected, so the strict rejection check failed. The statement and its comparisons were excluded from the report. This result is retained, not recategorized as a perfect score.

The missing-information run actually routed through broaden_search, refine_comparison, and verify_with_limitations. The three-paper success run took about 179 seconds. The six-paper evidence-rich static run took about 401 seconds and yielded five verified findings; compact context took about 139 seconds and yielded three. Both context runs used the same six-paper discovery limit, but K and section preferences differ. These are individual local measurements, not controlled latency estimates or independent scientific validation.

`scripts/validate_demo.py` records this smaller presentation cohort. Its explicit `--reuse-completed` option can rescore already saved real-model measurements; each reused measurement is labelled. Research requests never use this mechanism or substitute saved outputs for inference. A development wide dynamic run was interrupted during latency tuning and is recorded separately under artifacts/model-checks/.
