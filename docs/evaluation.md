# Actual model evaluation

`python -m contradiction_lab evaluate` executes eight scenarios in both workflows, followed by a compact/evidence-rich comparison. All inference runs through Ollama. Source documents contain no extraction annotations.

Scenarios cover a contextual-disagreement check on the training-volume question, the main success question, ambiguity, an unrelated question, a one-paper date filter (`date_to` 2005, leaving only Campos 2002), injected unsupported text, an invalid citation, provider outage, and synonym discovery. Fault injections are explicitly marked in raw runs and are never part of public source documents.

The harness records expected and observed report status, clarification, verified-claim minimums, fault rejection, comparison membership, adaptive bounds, model calls, actual input/output token counts, latency, errors, and routing. Every raw run is saved. Failed checks remain failures; they are not removed to improve the summary.

The two context configurations use top-K 4 with abstract preference and top-K 8 with methods/results preference. Both K and ranking preferences change, so differences cannot be attributed solely to K. Compare retrieved evidence, verified findings, tokens, and timing. Run `scripts/compare_settings.py` for a separate K-only change and the two requested routing-setting changes.

These are repeatable behavioral expectations, not human-reviewed scientific labels. The verifier is the same model as the extractor. Structural exclusion of unverified claims is not an independent hallucination metric. Do not claim extraction F1 based on exact generated wording, or scientific classification accuracy based on these seven abstracts. Add domain reviewers, real opposing study pairs, and held-out data before making those claims.

`pytest` uses explicit test mocks for model calls while running real LangGraph and Chroma. Passing tests does not substitute for Ollama integration runs. Historical replay artifacts are archived separately and are not current results.

## Recorded presentation validation

Gym corpus, recorded November 24, 2026 with qwen3:8b and nomic-embed-text through Ollama on an RTX 4060 laptop GPU: **7/8 strict behavioral checks passed** (`artifacts/evaluation/summary.json`, raw runs alongside).

| Scenario | Workflow | Status | Result | Time |
|---|---|---|---|---|
| success-static (7 papers) | static | evidence_found, 5 verified claims | pass | 75 s |
| success-dynamic (3 papers, frequency question) | dynamic | evidence_found, 3 verified; 2016 vs 2019 frequency = contextual_disagreement | pass | 46 s |
| ambiguity ("Does it work?") | dynamic | insufficient_evidence, clarification | pass | 2 s |
| uncertainty (off-topic) | dynamic | insufficient_evidence, no papers above the 0.6 cutoff | pass | 4 s |
| invalid-citation | static | injected citation rejected | pass | 23 s |
| missing-information (date_to 2005) | dynamic | limited_evidence via broaden_search, refine_comparison, verify_with_limitations | pass | 38 s |
| unsupported-claim | static | injected claim qualified (partial), not rejected; excluded from report | **fail** | 28 s |
| compact-context (top-K 4) | static | evidence_found, 2 verified | pass | 24 s |

The failure repeats the grassland result: the verifier recognised the injected universal statement as stronger than the passage but returned partial rather than no. The strict check is kept. Single runs; timings are individual measurements after model warm-up, not controlled latency estimates.

An earlier exploratory run of the volume question showed the verifier rating Heaselgrave 2019's no-effect claim as partial, because the same abstract reports moderate-to-large effect sizes for higher volume; that claim was excluded.

The previous grassland corpus results are archived in `artifacts/grassland-v1-evaluation/` and must not be presented as measurements of the current corpus.
