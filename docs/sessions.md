# Sessions

A session is one conversation about one research question. It is stored as a single document in the relational database: the question, the research options, a pointer to the research run, the current state, and an ordered list of messages.

## The handoff between the two AI services

Each session is bound to exactly one research run. This is the boundary between the two AI services:

```
 Phase 1: research                              Phase 2: follow-up
 ─────────────────                              ──────────────────
 question ─► session "researching" ─► research service runs
                                         │
                      session "ready" ◄──┘ (or "needs clarification" / "failed")
                                         │
 follow-up message ──────────────────────┴─► follow-up agent reads the finished run
```

- **Phase 1** is the only time evidence is gathered. The research service searches the article library, extracts and verifies findings, and stores the run.
- **Phase 2** starts when the run completes. Every later message goes to the follow-up agent, which can only read that run. It never searches or adds evidence.
- To ask about something new, the user starts a new session. Keeping one run per session means every answer in a conversation can be traced back to the same verified evidence.

## States

| State | Entered when | Follow-ups allowed |
|---|---|---|
| *researching* | The session is created | No (409) |
| *ready* | The run completes with a report | Yes |
| *needs clarification* | The planner found no identifiable exposure and outcome; the report carries a clarifying question and suggested specific questions | No (409); a suggestion starts a new session |
| *failed* | The run raised an unrecoverable error | No (409) |

State changes are made only by the session service: *researching* changes once, when the background job finishes.

## Messages

Messages alternate between the user and an assistant, and each has a kind:

| Kind | From | Contains |
|---|---|---|
| Question | User | The research question |
| Research | Research service | A one-line headline (status, number of verified findings, disagreements found) and the run identifier; the full report is read from the run |
| Follow-up | User / follow-up agent | The question, then the answer with its grounding status (grounded, not answerable, withheld), cited findings and passages, and token counts |

Earlier grounded question-and-answer pairs from the same session are passed back to the follow-up agent as conversation history (at most three), so it can resolve references like "that study".

## Listing

The session list is a summary view (title, state, run, created and updated times, message count) ordered by last update, which the web interface shows in its sidebar.
