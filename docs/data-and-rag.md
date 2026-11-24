# Data, retrieval, and provenance

## Public corpus

The offline corpus is six genuine publications, with short verbatim quotations rather than invented papers or fabricated full-text API responses. The snapshot identifies itself as `source_checked_excerpt`, not as a cached OpenAlex response. Extractions are AI-authored replay annotations, pending independent human review.

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

## Preparation and live ingestion

OpenAlex provides cross-disciplinary discovery and inverted-index abstracts. Europe PMC enriches biomedical/life-sciences records, abstracts, PMCID availability, and licensed full-text XML. Provider adapters normalize records to `Paper`; DOI normalization precedes deduplication, followed by provider identity and conservative title/year matching. Provenance, licenses, dates, URLs, and original cache timestamps remain attached.

Full-text XML preserves section headings and paragraph text; unsafe declarations and oversized responses are rejected. Missing abstracts and restricted full text remain missing. Raw responses are cached locally to make provider failures inspectable. Metadata-only passages are not treated as scientific findings.

## Chunks, embeddings, and vector database

Live text uses section-aware character boundaries approximating 550 tokens with 75-token overlap (four characters/token heuristic). Abstracts are kept separate from full-text sections; no chunk mixes papers. Exact source substrings and character offsets are preserved. Every passage carries paper ID, title, DOI, publication year, section, source type, source URL, chunk position, and SHA-256 content hash.

The offline excerpts are intentionally shorter than production chunks; they exercise contracts and orchestration, not realistic full-paper retrieval difficulty.

Two embedding paths are explicit:

1. **Offline lexical baseline:** stable signed token hashing into 384 dimensions, normalized cosine similarity, small controlled word aliases. This is not a trained semantic model. Persistence and vector retrieval are real, but synonym understanding is limited.
2. **Semantic path:** Sentence Transformers `sentence-transformers/all-MiniLM-L6-v2`, normalized embeddings, and persistent Chroma cosine retrieval. Model weights require installation/download and were not available in the build environment.

Passage text plus paper title is embedded. Passage text itself remains unchanged for citations. Hybrid ranking combines nonnegative vector similarity, exact term overlap, title relevance, and small context-mode preferences. Candidate-paper scope and per-run namespaces prevent cross-query contamination. SQLite's small vector store scans scoped vectors; it is appropriate only for the compact demo. Chroma is the intended larger local store.

## Context configurations

Compact uses top four passages and an abstract preference; evidence-rich uses top eight and prefers methods/results. Selection respects an approximate context-payload limit; each live structured request additionally checks its complete prompt and schema budget. Per-paper extraction avoids sending the whole corpus to every node. No long conversation history is retained.

Adding titles to retrieval metadata fixed an observed failure where a relevant abstract used “biomass” but the query used “productivity.” A remaining botanical-heterogeneity synonym query still returns no evidence in replay; it is kept as a known retrieval failure. Semantic embeddings may help, but improvement has not been measured here.

## Grounding chain

`comparison → claim IDs → passage IDs → paper ID/DOI/provider/URL`

Verification checks that the paper exists, source identity was observed in a snapshot/provider record, every passage belongs to that paper, all passage metadata/text match canonical ingested content, and hashes are intact. Replay support checks the exact cached extraction including study fields; live support uses a structured model judgment. Only `verified` claims enter synthesis. Partial support is inspectable as `qualified` but excluded from scientific comparisons rather than printed unmodified.

`source_resolves` is a compatibility field from the plan: here it means provider/snapshot identity was established. `source_check` makes that scope explicit. It does **not** mean a fresh HTTP DOI redirect was checked, nor that the paper is scientifically correct. The replay verifier is not an independent human entailment judge.
