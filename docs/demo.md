# Demo script

A live walkthrough of about 15 minutes. Every question below is typed freely into the app; none is a preset. Each was run on the real model on November 24, 2026 and behaved as described. Times are for the RTX 4060 laptop with the model already loaded.

## Before you start (5 minutes before)

1. Start Ollama and the app server: `.venv\Scripts\python -m contradiction_lab serve`, then open http://127.0.0.1:8000.
2. Check the dot next to "Contradiction Lab" in the sidebar is **green** (model ready).
3. **Warm the model**: run any question once. The first run after loading takes about 85 seconds; warm runs take about 45–60 seconds.
4. Leave the settings at **Adaptive** and **3 papers**.
5. Keep one finished session in the sidebar as a fallback. If a live run stalls, open it and say it was run earlier.

## 1. The problem and the promise (1 minute)

Open **New research**. Point out:
- "Answers come only from the 11 articles in the library": the system cannot use anything it was not given.
- The two settings: workflow (adaptive or fixed steps) and how many papers to compare.

> Studies on the same question often disagree. This tool does not pick a winner. It shows what each study found, checks every finding against the source text, and explains why they might differ.

## 2. A real disagreement: training frequency (3 minutes)

**Type:** `how often should i train each muscle to grow`

While it runs (about 50 seconds), talk through the live trace:
- **plan**: the model turns a casual question into search terms;
- **find papers / retrieve passages**: the vector search picks the papers and the exact text the model may read;
- **extract findings**: one structured finding per paper;
- **review directions**: a second pass, with reasoning, checks whether each effect goes up, down or nowhere;
- **compare / verify**: rules label each pair; every finding is checked against its source;
- **assess sufficiency** (adaptive only): the routing decision is shown with its reason.

**Expected result:** *Evidence found*, with **Schoenfeld 2016** ("training each muscle more often led to more muscle growth") against **Schoenfeld 2019** ("made no detectable difference"), labelled a **contextual disagreement**.

Point out:
- Each finding is a plain sentence with **the paper's own words** underneath.
- **Why they might differ**: differences in study design and conditions (the 2019 analysis pooled more studies and looked at volume-equated training).
- The caveat: "no detectable effect" is not proof of no effect. The system never calls this a contradiction.
- The volume paper in the result is labelled "different questions": it studies something else, so it doesn't count against either.

## 3. Follow-up questions in the same session (2 minutes)

Type these into the box at the bottom of the session:

1. `Why do the 2016 and 2019 papers disagree?`
   *Expected:* an answer built only from this session's evidence, with clickable citations. Click a quote citation to show the passage.
2. `Does creatine increase muscle growth?`
   *Expected:* refused. "This run's evidence does not answer that."
3. `Were any findings excluded?`
   *Expected:* says all findings passed verification.

> The research service gathered the evidence once. From here the follow-up agent takes over, and it can only read that evidence; its answers are shown only if every citation belongs to this session.

## 4. More free-typed questions (4 minutes)

Start each from **New research**:

| Type this | What happens | What it shows |
|---|---|---|
| `does protein help build muscle` | Morton 2018 (a 49-trial meta-analysis: protein supplements enhanced gains) against Erskine 2012 (a trial: no added benefit): contextual disagreement | The question everyone asks, answered with both sides and why they might differ (a pooled analysis versus one 12-week arm-training trial in untrained men) |
| `how long should i rest between sets` | Schoenfeld 2016 (3 minutes beat 1 minute) against Ahtiainen 2005 (2 and 5 minutes gave similar gains): contextual disagreement | A "how" question works too |
| `is lifting heavy better than light weights for building muscle` | Campos 2002 (heavier training gave more growth) against Mitchell 2012 (a lighter load lifted to failure gave similar growth): contextual disagreement | Everyday wording ("heavy", "light") is mapped to the research concept (load) |
| `do more sets build more muscle?` | The two Schoenfeld volume papers **agree** that more sets give more growth | Agreement is reported as plainly as disagreement |
| `does creatine help muscle growth` | *Insufficient evidence*: the library has no creatine study, and the findings it did retrieve (including the protein meta-analysis) are set aside as not answering the question | It will not answer with related-but-wrong evidence |
| `Is lifting good?` | *Needs clarification*, with three clickable, specific questions | Vague questions get help, not a guess. Click one to start a new session |

If time is short, do the protein, creatine and vague rows.

## 5. The library (2 minutes)

Click **Articles** in the sidebar.
- Eleven real papers across five topics (volume, frequency, load, rest between sets, protein), each with authors, journal, year and study design.
- **Search** `training twice a week`: the library search ranks articles by their best-matching passage and shows it.
- Open an article: its full published abstract and a **Read on PubMed** link. Every finding in a report traces back to an article like this.

## 6. How we know it works (2 minutes)

Click **Evaluation**: 8 of 8 strict real-model checks pass. Be candid that one of them (rejecting a planted overstatement, "every lifter doubles their muscle mass") failed in three earlier recordings; the claim was always kept out of the report, but the strict check is unstable, and two passing runs do not prove it is fixed.

Mention what the testing found and fixed today: the system once asked "Does creatine help muscle growth?" to clarify instead of searching, once lost papers when the planner shortened a question to one word, once answered a creatine question with training findings and later with the protein meta-analysis, and once recorded the heavy-load result backwards. Each was fixed with a rule or a tightened instruction and re-tested, not by hand-tuning the demo.

Optionally open **API docs** in the sidebar footer: the interface uses only this REST API.

## If something goes wrong

| Symptom | What to do |
|---|---|
| Red status dot | Ollama is not running or a model is missing. Start Ollama and refresh |
| "The model is busy" | Another run is still going; wait for it to finish |
| A run takes over 2 minutes | The model is reloading. Open the fallback session and talk through it |
| A result differs from this script | Say so. The model's wording varies between runs; the rules and checks do not. Use the trace and verification table to explain what happened |

## Questions you may be asked

- *Why not just ask a chatbot?* It would answer from memory, without sources, and could invent studies. Here every finding is quoted, verified and linked.
- *Why does it not say which study is right?* A disagreement often comes from different conditions; the tool shows them rather than adjudicating.
- *Could it hallucinate?* The model can misread, which is why every finding is checked against the source, labels are decided by rules, and follow-up answers are withheld if they cite anything outside the evidence. Same-model verification is a known limitation.
- *What would you do next?* Full-text papers, automatic retraction checks, an expert-labelled answer key, a separate verifier model, and repeated runs to measure variance.
