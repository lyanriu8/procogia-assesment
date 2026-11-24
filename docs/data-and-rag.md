# Data, retrieval, and provenance

## Public corpus

The preloaded corpus is six genuine publications, with short verbatim quotations rather than invented papers or fabricated full-text API responses. The snapshot identifies itself as `source_checked_excerpt`, not as a cached OpenAlex response. Findings are extracted by the running LLM; no source annotation is used as an answer.

| ID | Publication | DOI | Evidence scope |
|---|---|---|---|
| `tilman1996` | Tilman, Wedin & Knops, productivity/sustainability in grasslands | `10.1038/379718a0` | Abstract finding and experimental-design fragment |
| `hector1999` | Hector et al., European grassland diversity/productivity | `10.1126/science.286.5442.1123` | Abstract finding and location fragment |
| `wagg2022` | Wagg et al., long-term biodiversity/stability relationships | `10.1038/s41467-022-35189-2` | Abstract finding/duration and short Methods location excerpt |
| `tilman2006` | Tilman, Reich & Knops, decade-long grassland stability | `10.1038/nature04742` | Abstract finding and design fragment |
| `pfisterer2002` | Pfisterer & Schmid, diversity-dependent production/stability | `10.1038/416084a` | Abstract resistance finding |
| `yachi1999` | Yachi & Loreau, insurance hypothesis | `10.1073/pnas.96.4.1463` | Theoretical result and model-method fragment |

The selected primary productivity findings do not demonstrate a universal contradiction. Temporal stability and resistance to perturbation are different outcomes. The theoretical model is explicitly not an empirical experiment. No synthetic positive/negative pair is passed off as a real pair of papers. The genuine/contextual disagreement categories are demonstrated with separately identified synthetic rule tests until suitable independently labelled real pairs are added.

### Source checks

The source excerpts were checked using publisher/indexed primary-source pages on November 7, 2026 in America/Vancouver. IDs, DOI, authors and snippets can be rechecked at:

- https://www.nature.com/articles/379718a0
- https://pubmed.ncbi.nlm.nih.gov/10550043/
- https://www.nature.com/articles/s41467-022-35189-2 and https://pubmed.ncbi.nlm.nih.gov/36517483/
- https://pubmed.ncbi.nlm.nih.gov/16738658/
- https://www.nature.com/articles/416084a
- https://pubmed.ncbi.nlm.nih.gov/9990046/

Some publisher and PMC direct page requests returned redirects or bot challenges; search-indexed primary-source text was used to check those excerpts. This does not imply a direct full-document API download. License is unknown unless explicitly recorded. Public abstract visibility does not grant a full-document redistribution license. Live full-document fetching is restricted to recognized permissive licenses and provider access flags.

## Current ingestion and retrieval

Source documents contain no cached extraction annotations. Qwen reads the selected passages on every run. The default semantic encoder is nomic-embed-text through Ollama, with search_document/search_query prefixes, and Chroma is the only production vector backend. Ranking supplements semantic similarity with keyword/title matches and section preferences. Embeddings are reusable; extraction outputs are not substituted from previous runs.

External OpenAlex/Europe PMC discovery remains available through config.live.json. Exact chunks preserve sections, offsets, paper IDs, DOI/URLs, and content hashes. Missing scientific fields stay null. Only owned, intact passages and fully supported claims enter report assembly. The same-model verifier is not independent human adjudication.
