# Follow-up agent

The follow-up agent answers questions about one finished research run. Technically it is a **single structured language-model call wrapped in deterministic grounding checks**: the model proposes an answer with citations; code decides whether the answer may be shown.

## What it reads

A context document assembled from the stored run, and nothing else:

- the papers in the report (title, year, first author, study design);
- every extracted finding, **including excluded ones**, with its verification status and the verifier's reason;
- every comparison with its label, explanation, context differences and caveats;
- the exact quoted passages behind the report;
- the report's limitations;
- up to three earlier grounded question-and-answer pairs from the same session.

It has no search, no tools and no access to other runs, so it cannot bring in new evidence.

## What it returns

A JSON object constrained by a schema: whether the question is answerable from this run, the answer (two to five sentences), the identifiers of the findings it relied on, and the identifiers of the passages it relied on. The instructions tell it to use only the supplied evidence, refer to papers by author and year, describe what studies report rather than give training or medical advice, and say when a question cannot be answered.

## Grounding checks

| Condition | Shown to the user |
|---|---|
| Not answerable | A fixed message: this run's evidence does not answer that; start a new investigation |
| Answerable, but cites nothing, or cites any finding or passage that is not in this run | The answer is **withheld** and replaced by an explanation |
| Answerable, and every citation belongs to the run | The answer, with clickable citations |

The checks are set-membership tests on identifiers, so they are exact. They prove that an answer stays within the run's evidence. They do **not** prove that each sentence is a correct reading of that evidence: in testing, one answer suggested "different populations" as a reason for a disagreement, which the passages only partly support.

## Where it sits

The session service invokes the agent only when a session is *ready*, under the same one-job-at-a-time model lock as research. Answers take about 5–8 seconds on the test laptop. Each question and answer is stored on the session with its status, citations and token counts.
