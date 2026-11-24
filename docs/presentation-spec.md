# 30-minute client presentation and Q&A

Use `assessment-answers.md` as the complete speaking reference, not a script to read verbatim. The emphasis is the recommendation, evidence trail, observed behavior, and honest limitations.

## Presentation agenda

| Time | Segment | What to show/say |
|---|---|---|
| 0–3 min | Client problem and recommendation | Why comparing study context matters; intended R&D users; evidence navigation, not scientific adjudication |
| 3–6 min | Business value and success | Analyst baseline and usefulness study proposed; measured pipeline metrics versus unproven ROI |
| 6–10 min | Data and RAG | Six real sources, excerpt provenance, abstract/full-text distinction, unknown fields, vector/metadata design |
| 10–14 min | Agent architecture | Shared schemas and skills; static graph; conditional dynamic branches and bounded retries |
| 14–19 min | Workflow demos | Successful fixed path; adaptive full-text branch; out-of-corpus abstention; inspect passages and exclusions |
| 19–23 min | Context experiment and evaluation | Actual compact/rich outputs, metrics/denominators, injected fault, retained synonym failure |
| 23–26 min | Infrastructure and model trade-offs | Local-first app, optional LangGraph/Chroma/semantic/Ollama paths; runtime installation/validation limitations |
| 26–29 min | Lessons and next steps | Title metadata helped; more retries need not help; independent human review and real contradiction labels are missing |
| 29–30 min | Recommendation and disclosure | Narrow pilot, reviewer signoff, held-out evaluation; explain AI coding/source-checking assistance |

## Before presenting

- Activate `.venv` and run `python -m pytest -q`.
- Run `python -m contradiction_lab.evaluation.runner --workflow both`.
- Review `artifacts/evaluation/summary.json` and `report.md`; do not replace measured values with target metrics.
- Run `python scripts/compare_settings.py` and inspect the current raw observations.
- Start `python -m contradiction_lab serve`; verify the report, trace, sources, evaluation, and export in a real browser on the presentation machine.
- Decide whether the presentation is offline replay, LangGraph replay, or live inference; state that choice before showing it.
- For LangGraph/Chroma: install `.[dev,agents]`, use `config.langgraph-replay.json`, and confirm the previously skipped integration tests now pass.
- For live inference: validate the model download/digest, Ollama service, API credentials, provider access, semantic embedding download, and the actual query. Do not claim those paths were already validated in the sandbox.
- Independently review the six source excerpts and annotations. They are not yet human-reviewed scientific gold.
- Keep raw cached outputs as the fallback if a provider or model is unavailable; clearly announce the switch to replay.

## Exact demonstrations

### A. Successful static run

```sh
python -m contradiction_lab research --workflow static --output artifacts/demo-static.json
```

Show the fixed eight-node sequence, verified findings, unknown methods/effect sizes, agreement, apparent differences in outcomes, and the supporting passages. Do not manufacture a genuine scientific contradiction in these papers.

### B. Adaptive retrieval on the same evidence base

```sh
python -m contradiction_lab research --workflow dynamic --output artifacts/demo-dynamic.json
```

Show the sufficiency node, accessible-full-text attempt, adaptive counter, and return to the shared comparison/verification/report path. Distinguish “attempted to retrieve context” from “proved a scientific explanation.”

### C. Uncertainty and bounded abstention

```sh
python scripts/run_dynamic_demo.py
```

Show `broaden_search → verify_with_limitations`. The selected corpus contains no relevant lunar-basalt/chlorophyll evidence. The report says insufficient evidence in this scope, not that research can never answer the question.

### D. Actual retrieval failure and fault containment

```sh
python -m contradiction_lab research 'Does botanical taxonomic heterogeneity enhance yield?'
python -m contradiction_lab.evaluation.runner --workflow both
```

Show the saved failed synonym cases and the deliberately injected unsupported-claim/invalid-citation/provider-error cases. Failure injection is internal to evaluation and always labelled in raw output; it is not fabricated source evidence.

## Q&A change exercises

### Retrieval top-K: 4 → 8

```sh
python -m contradiction_lab research --workflow static --top-k 4
python -m contradiction_lab research --workflow static --top-k 8
```

The measured replay example changes verified findings from three to five and comparisons from three to ten. Inspect which evidence IDs changed, not just counts. The two *context-mode* experiment configurations also change section preferences, so those results cannot be attributed to K alone. Model inference tokens remain zero in replay; evidence payload estimates are a different quantity.

### Adaptive allowance: 1 → 2

Use the uncertainty query in `scripts/compare_settings.py`. Both settings broaden once and abstain because no useful new action remains. The limit is a maximum, not a requirement to perform futile work. The observed result is no improvement in evidence, not an assumed increase in quality.

### Comparable-pair threshold: 1 → 8

```sh
python -m contradiction_lab research --min-comparable-pairs 1
python -m contradiction_lab research --min-comparable-pairs 8
```

The stricter requirement exceeds the available comparable findings and returns limited evidence after bounded attempts. Explain the final post-verification gate; counting unverified claims is not sufficient. Re-run and inspect the current saved result rather than assuming the threshold must improve correctness.

## Likely discussion questions

- **Why not one prompt?** Specialized typed boundaries and independent verification make failures observable; this is an engineering decomposition, not a claim that more agents inherently improve quality.
- **Is the default vector store semantic?** No. It is an explicit lexical baseline. The optional Sentence Transformers/Chroma path must be tested separately.
- **What does “verified” mean?** Established source identity, intact owned passages, and configured support checks; not scientific truth or independent human review.
- **Why not report all qualified claims?** Partially supported text must be rewritten or reviewed before synthesis; printing it unchanged could overstate the evidence.
- **Does the perfect pair score prove genuine contradiction detection?** No. Labelled real-source pairs cover agreement/apparent differences. Genuine/contextual protocol scores are synthetic and separately identified.
- **What is the biggest missing validation?** Independent domain annotations and held-out real opposing findings, followed by actual model/semantic/integration measurements.
- **What would you change first?** Validate the full runtime on the demo machine, obtain human labels, and test semantic retrieval on the preserved vocabulary failure before adding scale.
