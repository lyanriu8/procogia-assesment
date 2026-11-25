# Evaluation

Evaluating a system built on a language model is harder than testing ordinary code: outputs are open-ended, small prompt or model changes shift behaviour, and there is no single correct string to compare against. The project therefore uses two separate layers of checks, and keeps their meanings apart.

## Layer 1: automated tests (mocked model)

A test suite of 84 tests runs the real web server, the real processing graph and the real vector database, but replaces every language-model call with a scripted reply. This isolates the deterministic machinery and makes it repeatable in seconds. It covers:

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

November 24, 2026, Qwen3 8B and nomic-embed-text on an RTX 4060 laptop GPU, recorded on the final code (after the robustness fixes below): **8 of 8 strict checks passed.**

| Scenario | Workflow | Outcome | Result | Time |
|---|---|---|---|---|
| Main question, 7 papers | static | Evidence found, 5 verified findings | pass | 81 s |
| Main question (frequency), 3 papers | dynamic | Evidence found, 3 verified; Schoenfeld 2016 vs 2019 = contextual disagreement | pass | 42 s |
| Vague question | dynamic | Clarification with three suggestions | pass | 5 s |
| Off-topic question | dynamic | Searched, no papers above the threshold, broadened once, stopped | pass | 9 s |
| Invalid citation | static | Injected citation rejected | pass | 26 s |
| Date filter (to 2005) | dynamic | Limited evidence after broadening and refocusing | pass | 40 s |
| Unsupported claim | static | Injected overstatement rejected; excluded from the report | pass | 29 s |
| Compact context | static | Evidence found, 2 verified | pass | 30 s |

**Read the 8/8 with care.** The unsupported-claim check failed in the three earlier recordings (the verifier answered *partial* rather than *no*; the claim was still excluded from the report) and passed in the two most recent ones. Today's changes may have helped, but two runs cannot separate an improvement from ordinary run-to-run variation, so treat this check as unstable.

## Free-typed questions

Because the demo relies on typing questions naturally, seven everyday phrasings were also run on the real model. The first round exposed four problems, each fixed with a rule in code and re-tested:

| Question | First result | Fix | Final result |
|---|---|---|---|
| "do more sets build more muscle?" | No papers found: the planner shortened it to "sets", which fell below the similarity threshold | Discovery also scores the user's own question | The three volume papers; two agree |
| "does creatine help muscle growth" | Asked for clarification; after that fix, answered with unrelated training findings | Questions with three or more meaningful words are always searched; findings that do not address the question are set aside | Insufficient evidence, with the set-aside findings noted |
| "is training to failure necessary" | Asked for clarification | Same rule | Mitchell 2012 vs Campos 2002, contextual disagreement |
| "is lifting heavy better than light weights…" | Missed the heavy-load paper; later recorded its direction backwards | IDF-weighted title matching and load synonyms; direction reviewer given the domain's worked examples | Mitchell 2012 vs Campos 2002, correct directions, in two runs |
| "how often should i train each muscle to grow" | Worked | — | Schoenfeld 2016 vs 2019, contextual disagreement |
| "does trainnig frequncy matter for hypertrophy" (typos) | Worked | — | Same as above |
| "best way to get bigger arms?" | Limited evidence, one paper | — | Honest limited result |

The model's wording and occasionally its pair judgments vary between runs (one frequency run labelled the pair "insufficient context" instead of a disagreement), so results in a live demo can differ slightly from this table.

Two earlier problems are recorded rather than hidden. The off-topic case once passed for the wrong reason (the planner asked for clarification instead of searching, and the check only counted findings); the check now also requires that no clarification was requested. The same planner behaviour briefly returned when the planner was given the corpus vocabulary for suggestions, and was fixed before this recording.

Follow-up answers are not part of the scored scenarios. They were spot-checked on the real model: a "why do these studies disagree" question was answered with valid citations in about 8 seconds, a question about creatine was refused as not answerable, and a question about excluded findings initially repeated the previous answer until the instructions were tightened.

## Context configurations on one query

Same question ("Is training a muscle more times per week better for muscle hypertrophy?"), static workflow, only the passage budget changed (recorded with the scenarios above; section preference also differs, see above):

| Configuration | Passages | Verified findings | Input tokens | Output tokens | Time |
|---|---|---|---|---|---|
| Evidence-rich (top-K 12) | 12 | 4 | 19,277 | 2,888 | 78 s |
| Compact (top-K 4) | 4 | 2 | 8,528 | 1,099 | 27 s |

Compact context cut input tokens by 56% and time by 65% but halved the verified findings: fewer passages meant fewer papers reached extraction. The raw-articles baseline below is a third configuration: everything in one call.

## Answer-key scoring

`scripts/score_answer_key.py` scores the pipeline against a key of the correct exposure and direction for each of the 11 papers and the expected behaviour, required papers and pair labels for nine free-typed questions. **The key is a draft written with AI assistance and not yet confirmed by a person**, so these are not accuracy figures.

First run (qwen3:8b, one repeat): behaviour 9/9, exposure 12/13, direction 12/13, key pairs 6/6 (strict and lenient), no required paper missing. **The one failure:** on the frequency question, Heaselgrave 2019 (a volume study) was filed under training frequency with direction "unclear". The key does not accept that exposure, so the direction is not credited either. Details: `artifacts/answer-key/report.md`.

## Raw-articles baseline

To test whether the pipeline earns its complexity, `scripts/score_baseline.py` gives the same model one call containing every passage from all 11 papers, the same label definitions and domain hints, reasoning on, and the same name normalization, but no retrieval, direction review, rule-based labels or verification. It is scored with the same key (November 24, 2026, qwen3:8b, one repeat):

| Metric | Baseline | Pipeline |
|---|---|---|
| Behaviour (answer / abstain / clarify) | 9/9 | 9/9 |
| Exposure of reported findings | 13/14 | 12/13 |
| Direction of reported findings | 13/14 | 12/13 |
| Key pairs, strict / lenient | 6/6 / 6/6 | 6/6 / 6/6 |
| Invented citations | 0 | 0 by construction |
| Mean seconds per question | 231 (52–803) | 66 (4–169) |
| Input tokens per question | about 4,400 (one call) | about 700–19,000 (several calls) |

**On this library the baseline ties the pipeline on accuracy.** Both made the same single error (Heaselgrave 2019 under frequency, on different questions). The pipeline was about 3.5× faster, because reasoning over the whole library is slow on an 8B model; the baseline needed a 900-second timeout. The comparison is honest about what it shows: with 11 abstracts (about 4,400 tokens) the whole library fits in one prompt, so retrieval adds nothing to accuracy here. The pipeline's case rests on what the baseline cannot do: scale past the context window, run faster, show which passage supports each finding, and reject unverified claims before they reach the report. An accuracy advantage would need a library larger than the context window to test.

## What these results do not show

- **No confirmed accuracy figure.** The behavioural expectations and the draft answer key were written by the developer with AI assistance, not by independent domain experts.
- **Correlated verification.** The same model extracts and verifies, so it can make the same mistake twice.
- **Single samples.** Each scenario ran once; language-model output varies, so these are not pass rates.
- **Small coverage.** Eleven abstracts cannot establish general performance.

Next steps would be confirming the answer key with a domain expert, repeated runs to measure variance (`--repeats 3` on both scoring scripts), a library larger than the context window so the baseline cannot see everything, a different or stronger verifier model, and held-out papers.

Earlier results for the previous grassland corpus are archived separately and do not describe the current system.
