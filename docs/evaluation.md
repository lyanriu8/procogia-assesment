# Evaluation methodology and limitations

## Repeatable commands and artifacts

```sh
python -m contradiction_lab.evaluation.runner --workflow both
python -m contradiction_lab.evaluation.runner --workflow static
python -m contradiction_lab.evaluation.runner --workflow dynamic
python -m contradiction_lab.evaluation.runner --compare-context-configs
python scripts/compare_settings.py
python -m pytest -q
```

`src/contradiction_lab/data/cases.jsonl` is the versioned input. `artifacts/evaluation/summary.json` contains actual metrics, per-case decisions, configuration, model/prompt versions, and experiment outputs. Individual JSON files preserve raw runs and traces. `report.md` is the readable summary. These are measured offline replay results, not invented target scores.

## Dataset and ground truth

- Twenty research/protocol scenarios, each executed in static and dynamic modes: 40 research runs.
- Four separate synthetic comparison-rule cases: genuine, contextual, apparent, and insufficient evidence.
- Scenarios cover agreement, different outcomes, ambiguous requests, missing methods, insufficient papers, date filters, low retrieval budgets, API failure, invalid citations, unsupported claims, and a deliberately retained synonym failure.
- Source-study annotations and expected outputs were authored by an AI coding assistant and source-checked. **No independent human reviewer has signed off.** They must not be called human-labelled gold or used to certify scientific accuracy.
- Synthetic pairs use conspicuously synthetic systems, methods, and IDs. They never appear in the scientific source corpus or user reports.

No available human-labelled real contradiction dataset was fabricated to satisfy the plan's aspirational 20–30 manually reviewed cases. Completing independent review and adding real contradictory/contextual pairs remains a release gate for scientific performance claims.

## Metrics and denominators

| Metric | Implementation and interpretation |
|---|---|
| Retrieval recall@configured-K | Retrieved primary passage IDs / labelled relevant primary passage IDs per case; null if none are expected. K can differ by case. Not always recall@10. |
| Extraction precision/recall/F1 | Exact `(claim_id, statement)` tuples, compared with AI-authored source replay expectations. Field scores are separate. |
| Context-field F1 | Non-null labelled fields among outcome, direction, system, method, duration, exposure; exact value matching. Missing expected values are false negatives; additional non-null predictions count against precision. |
| Classification macro-F1 | Only explicitly labelled source-pair relationships; missing retrieved pairs use a `missing` prediction sentinel. Agreement is separate from the four disagreement categories. |
| Synthetic rule macro-F1 | Reported separately for four protocol fixtures; not scientific classification quality. |
| Source validity | Fraction of extracted claims with established source identity and intact owned passages; deliberately invalid citations count against it. Not live URL uptime. |
| Passage support | Fraction of extracted claims matching replay support or passing the configured verifier; injected unsupported statements lower it. Not human adjudication. |
| Unsupported final claim rate | Final claim IDs absent from verified IDs / final claims. Null for empty reports. This is a structural safety invariant, not an independent hallucination measure. |
| Routing accuracy | Correct first adaptive decision only where a case explicitly specifies a route. Remaining transitions are covered by unit tests. |
| Latency | Sum of instrumented node latency; context experiment separately records whole-run wall time. Single local runs are noisy and not production estimates. |
| Tokens/cost | Provider token counts for live calls; zero inference tokens in replay. Approximate serialized context payload size is reported separately. Hosted replay API cost is zero; total local compute cost is unmetered/null. |

Reported aggregates are per-case means over non-null observations. Expected-empty extraction cases receive perfect extraction F1 if nothing is extracted; consequently the mean is not a scientific claim-level micro-F1. Research pass/fail checks expected report status plus specified pair, routing, fault, and rejection behavior; passing a run does not mean every quality target is achieved.

## Observed failures and lessons

The known failure `r20-synonym-blind-spot` asks about botanical taxonomic heterogeneity and yield. The lexical discovery adapter does not map that phrasing to the small grassland corpus. Both workflows abstain rather than inventing evidence. This is labelled a discovery/retrieval failure, not “no relevant scientific literature exists.” More adaptive iterations do not fix missing vocabulary knowledge.

An earlier implementation ranked a relevant biomass abstract too low. Preserving and embedding parent-paper titles fixed the operational fault without rewriting the quoted source text. Tests also established that corrupt passages, foreign-paper citations, malformed structured output, wrong context fields, and unavailable models cannot silently enter synthesis.

## What the reported numbers do not prove

The corpus is tiny, repeatedly reused, and its extraction replay and expected annotations are not independent. Real-source labelled comparisons cover agreement and apparent disagreement; genuine/contextual scientific performance is **not measured**. Source-validity and support rates include deliberately injected faults. The same-model live verifier would also have correlated errors. No external model inference, semantic retrieval benchmark, browser rendering, or human usefulness study was completed in the build sandbox.

Before making performance claims: obtain two domain reviewers, adjudicate labels, freeze train/development/held-out corpora, include real opposing findings and outcome/unit ambiguities, repeat runs across domains/models, inspect failure components, and independently audit the final report passages. Measure human time saved and usefulness rather than only pipeline invariants.
