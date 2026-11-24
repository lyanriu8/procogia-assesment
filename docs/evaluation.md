# Evaluation

Evaluating a system built on a language model is harder than testing ordinary code: outputs are open-ended, small prompt or model changes shift behaviour, and there is no single correct string to compare against. The project therefore uses two separate layers of checks, and keeps their meanings apart.

## Layer 1: automated tests (mocked model)

A test suite of 75 tests runs the real web server, the real processing graph and the real vector database, but replaces every language-model call with a scripted reply. This isolates the deterministic machinery and makes it repeatable in seconds. It covers:

- data contracts and validation;
- retrieval ranking, token budgets and chunking;
- name normalization, the comparison rules (including that "effect versus no effect" can never become a contradiction) and the direction mapping;
- routing budgets, stop conditions and failure containment in the adaptive loop;
- the session lifecycle and handoff, including the 409 refusals while researching, for clarification sessions and when the model is busy;
- the article library (indexing, listing, detail, search);
- follow-up grounding: valid, foreign and missing citations, unanswerable questions, bounded history;
- clarification suggestions.

Passing tests show the plumbing is correct. They say nothing about model quality.

## Layer 2: real-model scenarios

A scenario harness sends real questions through the real local model and scores each run against **behavioural expectations**: not "is this the right sentence?" but "did the system act correctly?". Each run is saved in full (report, trace, token counts, timings) so failures can be inspected.

Every run is also checked for invariants:
- every finding in the report was verified;
- every comparison uses only verified findings;
- the model was actually called (token count above zero);
- the adaptive budget was respected.

| Scenario | What it checks |
|---|---|
| Main question, static and dynamic | Evidence found, at least two verified findings; in the dynamic run, at least one contextual disagreement |
| Vague question ("Does it work?") | A clarifying question is returned |
| Off-topic question | It searches (no clarification), finds no papers, and abstains |
| Date filter leaving one paper | Limited evidence, after the adaptive loop tries to compensate |
| Injected unsupported claim | A planted overstatement ("every lifter doubles their muscle mass") is rejected |
| Injected invalid citation | A finding citing a passage that does not exist is rejected |
| Compact context (fewer passages) | Still produces verified findings; compared with the evidence-rich setting |

**Fault injection** is how a missing answer key is partly worked around: you cannot measure a hallucination rate without labelled data, but you can plant a known bad claim and a known bad citation and check that the safeguards catch them. Injected faults are flagged in the saved runs and never enter the source documents.

A larger benchmark variant runs nine scenarios in both workflows (adding provider outage and synonym discovery) plus a compact versus evidence-rich comparison. In that comparison both the passage count and the section preference change, so differences cannot be attributed to passage count alone; a separate script changes only one setting at a time.

## Recorded results

November 24, 2026, Qwen3 8B and nomic-embed-text on an RTX 4060 laptop GPU, recorded after the architecture reorganization: **7 of 8 strict checks passed.**

| Scenario | Workflow | Outcome | Result | Time |
|---|---|---|---|---|
| Main question, 7 papers | static | Evidence found, 5 verified findings | pass | 74 s |
| Main question (frequency), 3 papers | dynamic | Evidence found, 3 verified; Schoenfeld 2016 vs 2019 = contextual disagreement | pass | 44 s |
| Vague question | dynamic | Clarification with three suggestions | pass | 4 s |
| Off-topic question | dynamic | Searched, no papers above the threshold, broadened once, stopped | pass | 9 s |
| Invalid citation | static | Injected citation rejected | pass | 24 s |
| Date filter (to 2005) | dynamic | Limited evidence after broadening and refocusing | pass | 38 s |
| Unsupported claim | static | Injected claim rated *partial* (qualified), not rejected; still excluded from the report | **fail** | 29 s |
| Compact context | static | Evidence found, 2 verified | pass | 25 s |

The failure is kept as a failure. The verifier recognized the planted statement as stronger than the source but answered *partial* rather than *no*; the report still excluded it, but the strict check requires outright rejection.

Two earlier problems are recorded rather than hidden. The off-topic case once passed for the wrong reason (the planner asked for clarification instead of searching, and the check only counted findings); the check now also requires that no clarification was requested. The same planner behaviour briefly returned when the planner was given the corpus vocabulary for suggestions, and was fixed before this recording.

Follow-up answers are not part of the scored scenarios. They were spot-checked on the real model: a "why do these studies disagree" question was answered with valid citations in about 8 seconds, a question about creatine was refused as not answerable, and a question about excluded findings initially repeated the previous answer until the instructions were tightened.

## What these results do not show

- **No scientific accuracy figure.** The expectations were written by the developers, not by independent domain experts; there is no labelled set of correct findings.
- **Correlated verification.** The same model extracts and verifies, so it can make the same mistake twice.
- **Single samples.** Each scenario ran once; language-model output varies, so these are not pass rates.
- **Small coverage.** Seven abstracts cannot establish general performance.

Next steps would be an expert-labelled answer key, repeated runs to measure variance, a different or stronger verifier model, and held-out papers.

Earlier results for the previous grassland corpus are archived separately and do not describe the current system.
