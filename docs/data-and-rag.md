# Data, retrieval, and provenance

## Public corpus

The preloaded corpus (`gym-hypertrophy-v1`) contains seven real publications on resistance training and skeletal muscle hypertrophy. Excerpts are exact sentences from the official PubMed records, fetched through NCBI E-utilities on November 24, 2026, and checked as exact substrings of each abstract when the corpus was built. Non-breaking and thin spaces are normalized to ordinary spaces; wording is unchanged. Sentences joined with ` … ` are separate exact sentences from the same abstract section. Each paper also records its PubMed publication types (randomized controlled trial, meta-analysis). Findings are extracted by the running LLM; no annotation is used as an answer.

| ID | Publication | DOI | Design | Abstract-level conclusion |
|---|---|---|---|---|
| `schoenfeld2017volume` | Schoenfeld, Ogborn & Krieger, *J Sports Sci* 2017 | `10.1080/02640414.2016.1210197` | Meta-analysis, 15 studies | More weekly sets, greater hypertrophy (graded dose-response) |
| `schoenfeld2019volume` | Schoenfeld et al., *Med Sci Sports Exerc* 2019 | `10.1249/MSS.0000000000001764` | RCT, 34 trained men, 8 wk | Hypertrophy follows a dose-response with volume |
| `heaselgrave2019` | Heaselgrave et al., *Int J Sports Physiol Perform* 2019 | `10.1123/ijspp.2018-0427` | RCT, 49 trained men, 6 wk, biceps | No significant between-group differences in muscle thickness; moderate-to-large effect sizes for higher volume |
| `schoenfeld2016frequency` | Schoenfeld, Ogborn & Krieger, *Sports Med* 2016 | `10.1007/s40279-016-0543-8` | Meta-analysis | Training twice a week beats once a week |
| `schoenfeld2019frequency` | Schoenfeld, Grgic & Krieger, *J Sports Sci* 2019 | `10.1080/02640414.2018.1555906` | Meta-analysis, 25 studies | Frequency does not meaningfully affect hypertrophy when volume is equated |
| `campos2002` | Campos et al., *Eur J Appl Physiol* 2002 | `10.1007/s00421-002-0681-6` | Training study, 32 untrained men, 8 wk | Heavier (low/intermediate repetition) training gave greater hypertrophy than light (high repetition) |
| `mitchell2012` | Mitchell et al., *J Appl Physiol* 2012 | `10.1152/japplphysiol.00307.2012` | Randomized within-subject, 18 men, 10 wk | A lower load lifted to failure gave similar hypertrophy to a heavy load |

The corpus contains three real disagreement clusters: training volume (two positive vs one no-significant-difference), training frequency (the same research group's 2016 positive result vs its 2019 volume-equated null), and load (heavier better vs similar when taken to failure). Comparisons across clusters involve different exposures and should be classified as apparent disagreements. The main demo question targets the frequency cluster, whose null finding is stated unambiguously. Heaselgrave 2019 reports non-significant differences but also moderate-to-large effect sizes for higher volume; in a real run the verifier rated its no-effect claim as only partially supported and excluded it, which is the intended conservative behaviour.

Excluded on purpose: Barbalho et al. 2019/2020, "Evidence of a ceiling effect for training volume…", was a natural counterpoint but is **retracted** (PubMed retraction notice, IJSPP 2020). The app does not yet check for retractions automatically.

### Domain vocabulary is data

The `domain` section of `data/corpus.json` holds the demo queries, the extraction hint (normalized outcome, exposure, population and design names), the direction examples, the outcome and exposure keyword maps used by `normalize_claims`, and the query aliases used for lexical retrieval scoring. Pipeline code contains no topic-specific vocabulary, so a new domain is a data change. The previous grassland corpus remains on the `main` branch and the `demo-ready` tag.

### Licensing

No excerpt has a verified open license, so every paper is abstract-only (`license: null`, `full_text_available: false`). The dynamic `retrieve_full_text` action is therefore never offered with the bundled corpus; it remains covered by a test that simulates a licensed paper and by live discovery mode. Public abstract visibility does not grant a full-document redistribution license.

## Current ingestion and retrieval

Source documents contain no cached extraction annotations. Qwen reads the selected passages on every run. The default semantic encoder is nomic-embed-text through Ollama, with search_document/search_query prefixes, and Chroma is the only production vector backend. Ranking supplements semantic similarity with keyword/title matches and section preferences (methods, results and conclusions in evidence-rich mode).

Paper discovery in corpus mode is gated by semantic similarity of at least 0.6 and ranked by semantic similarity plus half the query-term overlap with the title. A single-topic corpus compresses semantic scores (0.80–0.86 for every paper on the demo questions), so similarity alone ranked the wrong cluster first under a three-paper limit; the off-topic control question scored up to 0.48, which passed the previous 0.45 cutoff. Both values were set by inspecting these seven papers, not tuned on held-out data. Embeddings are reusable; extraction outputs are not substituted from previous runs.

External OpenAlex/Europe PMC discovery remains available through config.live.json. Exact chunks preserve sections, offsets, paper IDs, DOI/URLs, and content hashes. Missing scientific fields stay null. Only owned, intact passages and fully supported claims enter report assembly. The same-model verifier is not independent human adjudication.
