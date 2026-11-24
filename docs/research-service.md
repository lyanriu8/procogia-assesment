# Research service

The research service turns a question into a verified comparison report. Technically it is a **state machine expressed as a directed graph** (built with LangGraph): each node is a processing step, edges decide which step runs next, and one typed state object (papers, passages, findings, comparisons, verification results, errors, trace) is passed from node to node. Several steps call the language model; the rest are deterministic code.

## The graph

**Static workflow:** a fixed sequence of eight steps.

```
plan → find papers → retrieve passages → extract findings → review directions → compare → verify → build report
```

**Dynamic workflow:** the same steps, plus a decision point after extraction.

```
                                   ┌──────────── enough evidence ────────────┐
plan → find papers → retrieve → extract → assess sufficiency                 ▼
          ▲              ▲                    │                       review directions → compare → verify → report
          │              │                    ├─ broaden search ─► back to "find papers"           ▲
          │              └────────────────────┼─ fetch licensed full text ─► back to "retrieve"     │
          │                                   ├─ refocus retrieval ─► back to "retrieve"            │
          └───────────────────────────────────┴─ stop with limitations ─────────────────────────────┘
```

Each step records its start and end time, latency, the model's input and output token counts, retries and errors. These form the trace shown in the interface and stored with the run.

## The steps

**Plan** (language model, with a rule on top). Produces search terms and an interpretation of the question. It may ask for clarification when the question names no identifiable exposure and outcome (for example "Does it work?"), and then proposes up to three specific questions built from the corpus's vocabulary. Code overrides that choice whenever the question has three or more meaningful words (after removing stop-words): such questions are always searched, and finding nothing is reported later. In testing the model asked to clarify perfectly specific questions such as "does creatine help muscle growth", which is why the final say is a rule.

**Find papers** (deterministic). Scores every paper against both the planner's search term and the user's own question and keeps the better match, then applies a similarity threshold and a title-match bonus, up to the paper limit. Scoring the user's wording too means one poor rewrite cannot hide relevant papers: the planner once reduced "do more sets build more muscle?" to the single word "sets", which fell below the threshold. See [Article library and retrieval](rag.md).

**Retrieve passages** (deterministic). Ranks the selected papers' stored passages against the question and keeps the best ones within a passage count and token budget. These passages are the only text the models see. In the dynamic workflow, full-text passages are held back until the adaptive loop chooses to fetch them.

**Extract findings** (language model, then code). For each paper, the model returns at most one finding as a structured record: statement close to the source wording, whether the finding addresses what the question asks about, outcome, exposure, direction, study system, design, duration and conditions. Findings marked as not addressing the question are set aside and the report says how many; this stops, for example, a question about creatine from being answered with findings about training volume. Direction is asked as "what happens to the outcome when the exposure increases", which avoids sign confusion. Code then:
- rejects findings that reference another paper or unknown passages;
- links each finding to all of its paper's retrieved passages (broader than a single sentence, so verification can also check design and duration);
- replaces "not specified" style answers with an explicit unknown;
- maps outcome and exposure wording onto canonical labels using the corpus's keyword vocabulary (for example muscle thickness, cross-sectional area or "MT" all become *muscle hypertrophy*);
- records which fields are unknown.

**Review directions** (language model, reasoning enabled). One call reviews all findings and decides, for each, whether the outcome *increases*, *decreases*, *does not change* or *is not established* as the exposure increases. Its answer replaces the extractor's direction. It is given the domain's worked direction examples and told to translate indirect descriptions into the named exposure: without that, it read "low-repetition (heavier) training gave more growth than high-repetition (lighter) training" as an effect of *repetitions* and recorded the load effect backwards. The call must return exactly the set of findings it was given, or the step fails. This is the only step where the model's step-by-step reasoning mode is switched on, because turning it off brought back sign errors.

**Assess sufficiency** (rules, then optionally the model; dynamic only). Evidence is *enough* when there are at least two findings and at least one pair from different papers with the same outcome. Hard stops come first: a clarification request, a discovery failure with no findings, or any model error ends the loop. Otherwise the rules suggest an action, the model may choose any action from the permitted list, and code ignores any choice outside that list. Each action can run at most once; at most two actions run in total; a graph recursion limit is the final guard against loops.

| Action | Effect |
|---|---|
| Broaden search | The model rewrites the search using simpler synonyms while keeping exposure and outcome; returns to paper discovery |
| Fetch full text | Adds licensed full-text passages for papers that have them; returns to passage retrieval |
| Refocus retrieval | Re-ranks passages against "first extracted outcome + question"; returns to passage retrieval |
| Stop with limitations | Records why and continues to analysis with the evidence it has |

**Compare** (rules, then the model). All pairs of findings from different papers are compared (at most 21 pairs). Deterministic rules decide the label from the normalized fields:

| Situation | Label |
|---|---|
| Different outcome, exposure or units | *Different questions* (apparent disagreement, not comparable) |
| Same outcome, same direction | *Agreement* |
| Same outcome, opposite directions, known context differences | *Contextual disagreement* |
| Same outcome and exposure, one effect versus no detectable effect, known context differences | *Contextual disagreement* (divergence), with the note that a non-significant result is not an opposite effect |
| Same outcome, opposite directions, system, design and exposure all confirmed identical | *Candidate contradiction* |
| Anything else, including missing context | *Insufficient context* |

The model then judges all pairs in one call; the output schema fixes the array length to the number of pairs, so none can be skipped. The model's judgment can only downgrade a label to *insufficient context*, never upgrade it, and its one-sentence explanation is attached as a labelled model assessment.

**Verify** (code, then the model). For each finding, code first checks that the paper exists with an HTTPS source and a DOI or provider identifier, and that every cited passage belongs to that paper, matches the stored original exactly, and still has the same SHA-256 hash. Only then does the model judge whether the passages support every populated field (*yes*, *partial*, *no*, *unclear*). *Yes* gives **verified**, *partial* gives **qualified**, anything else **rejected**.

**Build report** (code). Only verified findings enter the report, and only comparisons whose two findings are both verified. The status is:
- **evidence found**: at least two verified findings and at least one usable pair (agreement, opposition or divergence);
- **limited evidence**: some verified findings but below those thresholds, or any error occurred;
- **insufficient evidence**: no verified findings.

Agreement and disagreement summaries are counts, not generated prose. Limitations are listed automatically: abstract-only sources, unknown fields, excluded findings, recorded errors.

## Failure handling

A model or provider error inside a step is caught and recorded in the run's state with the step that raised it. Safe defaults take over: a failed planner means "search the question as written", a failed router means "stop", a failed extraction means "no findings". The run continues to a report that carries the error as a limitation; nothing is substituted for the failed call.
