# Raw-articles baseline vs pipeline

**Key status: DRAFT.** Labels not yet confirmed by a person; do not report these as accuracy.

The baseline is one model call with every passage from all 11 papers, the same label definitions and domain hints, reasoning on, and the same name normalization; it has no retrieval, direction review, rule-based labels or verification.

| Metric | Baseline | Pipeline |
|---|---|---|
| Behaviour (answer / abstain / clarify) | 9/9 | 9/9 |
| Exposure of reported findings | 13/14 | 12/13 |
| Direction of reported findings | 13/14 | 12/13 |
| Key pairs, strict | 6/6 | 6/6 |
| Key pairs, lenient | 6/6 | 6/6 |
| Required papers missing | 0 | 0 |
| Invented citations (papers not in the library) | 0 | 0 by construction |
| Mean seconds per question | 230.8 | see answer-key report |

| Question | Repeat | Behaviour | Wrong directions | Pair labels | Invented |
|---|---|---|---|---|---|
| frequency | 0 | answer (ok) | - | schoenfeld2016frequency/schoenfeld2019frequency: contextual_disagreement (strict ok) | - |
| frequency-typos | 0 | answer (ok) | heaselgrave2019=positive (filed under training frequency) | schoenfeld2016frequency/schoenfeld2019frequency: contextual_disagreement (strict ok) | - |
| protein | 0 | answer (ok) | - | morton2018/erskine2012: contextual_disagreement (strict ok) | - |
| rest | 0 | answer (ok) | - | schoenfeld2016rest/ahtiainen2005: contextual_disagreement (strict ok) | - |
| load | 0 | answer (ok) | - | campos2002/mitchell2012: contextual_disagreement (strict ok) | - |
| volume | 0 | answer (ok) | - | schoenfeld2017volume/schoenfeld2019volume: agreement (strict ok) | - |
| creatine | 0 | abstain (ok) | - | - | - |
| off-topic | 0 | abstain (ok) | - | - | - |
| vague | 0 | clarify (ok) | - | - | - |
