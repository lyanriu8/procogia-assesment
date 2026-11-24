# Web interface

A **single-page application**: one HTML document with plain JavaScript and CSS, no framework and no build step, served by the API at `/`. It talks to the system only through the [REST API](api.md), so every view corresponds to an API resource. Its look follows Notion: a sidebar, pages with large titles and property rows, callout blocks, collapsible toggles and database-style tables. It follows the operating system's light or dark setting.

## Views and what they call

| View | Shows | API calls |
|---|---|---|
| **Sidebar** | New research, the Library (Articles with a count, Evaluation), the session list with state icons, a model status dot and a link to the API docs | `GET /api/sessions`, `GET /api/articles`, `GET /api/system/health` and `/readiness` (every 10 s) |
| **New research** | A greeting, two settings above the question box (workflow and number of papers, plus a removable date-limit chip when the "Before 2006" shortcut is used), the question box with a send button, a note that answers come only from the article library, and shortcut questions | `POST /api/sessions`, then opens the new session |
| **Session** | Title and properties (status, evidence, workflow, counts, run); the question; the research result; the follow-up thread; a message box | `GET /api/sessions/{id}`, `GET /api/runs/{id}` (every 1.2 s while researching), `POST /api/sessions/{id}/messages`, `DELETE /api/sessions/{id}` |
| **Articles** | A card per article (title, authors, journal and year, design tags, abstract preview) and a library search that ranks whole articles by their best-matching passage, showing that passage | `GET /api/articles`, `GET /api/articles/search` |
| **Article** | Title, authors, design tags, links to PubMed and the DOI, the full published abstract with its section headings, and a short details table (PubMed ID, licence, search-index status) | `GET /api/articles/{id}` |
| **Evaluation** | The latest real-model results with pass/fail per scenario | `GET /api/evaluation/latest` |

Navigation uses the URL fragment (for example `#/sessions/<id>` or `#/articles/<id>`), so views can be bookmarked and the browser's back button works.

## The session page

- **While researching:** a callout with a live list of completed processing steps, each with its time and token count, routing decisions in the dynamic workflow, and a spinner on the current step. The message box is disabled.
- **When ready:** a headline callout (evidence status, and any disagreement found), then findings, then comparisons, all written as plain sentences. Each finding is a sentence built from its direction, exposure and outcome (for example "Training each muscle more often led to more muscle growth.") above the paper's own words. Each comparison opens with a sentence for its label (for example "Schoenfeld 2016 found that training frequency affects muscle growth; Schoenfeld 2019 found no detectable effect.") followed by "Why they might differ" sentences built from the context differences, the caveats and the model's reading. The sentences are fixed templates filled with extracted values; nothing in them is generated. Real disagreements are expanded; other pairs are collapsed to one line. Limitations, sources (linking to the article pages) and every verification decision, including excluded findings, are collapsible.
- **Follow-ups:** each answer shows its citations as chips. Finding citations open the article page; passage citations expand the quoted text inline. Withheld or unanswerable replies are shown in a muted style with their explanation.
- **Needs clarification:** the clarifying question and the suggested specific questions as buttons, each starting a new session.

Two papers by the same author in the same year are labelled with the academic convention (2019a, 2019b).

## Safety

All server data is inserted into the page as text nodes, never as HTML, so passage or model text cannot inject markup or scripts. External links open in a new tab without access to the opener.
