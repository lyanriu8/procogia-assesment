# Article library and retrieval

Retrieval-augmented generation (RAG) means the language model answers from retrieved source text instead of from memory. In this system the retrieval side has three parts: a curated **corpus** of papers, an **article library** that stores their passages as vectors, and two **ranking stages** that decide which papers, and then which passages, the models may read.

## Corpus

Seven real publications on resistance training and skeletal muscle hypertrophy. Each passage is an exact sentence from the paper's official PubMed record, fetched through the NCBI E-utilities API on November 24, 2026 and checked as an exact substring of the abstract when the corpus was built. Non-breaking and thin spaces were normalized to ordinary spaces; wording is unchanged. Sentences joined with " … " are separate exact sentences from the same abstract section. Each paper also carries its DOI, PubMed ID, journal, authors and PubMed publication types. The corpus holds source text only; no answers or annotations.

| Publication | DOI | Design | Abstract-level conclusion |
|---|---|---|---|
| Schoenfeld, Ogborn & Krieger, *J Sports Sci* 2017 | 10.1080/02640414.2016.1210197 | Meta-analysis, 15 studies | More weekly sets, greater hypertrophy (graded dose-response) |
| Schoenfeld et al., *Med Sci Sports Exerc* 2019 | 10.1249/MSS.0000000000001764 | Randomized trial, 34 trained men, 8 weeks | Hypertrophy follows a dose-response with volume |
| Heaselgrave et al., *Int J Sports Physiol Perform* 2019 | 10.1123/ijspp.2018-0427 | Randomized trial, 49 trained men, 6 weeks, biceps | No significant between-group differences in muscle thickness; moderate-to-large effect sizes for higher volume |
| Schoenfeld, Ogborn & Krieger, *Sports Med* 2016 | 10.1007/s40279-016-0543-8 | Meta-analysis | Training twice a week beats once a week |
| Schoenfeld, Grgic & Krieger, *J Sports Sci* 2019 | 10.1080/02640414.2018.1555906 | Meta-analysis, 25 studies | Frequency does not meaningfully affect hypertrophy when volume is equated |
| Campos et al., *Eur J Appl Physiol* 2002 | 10.1007/s00421-002-0681-6 | Training study, 32 untrained men, 8 weeks | Heavier (low/intermediate repetition) training gave greater hypertrophy than light (high repetition) |
| Mitchell et al., *J Appl Physiol* 2012 | 10.1152/japplphysiol.00307.2012 | Randomized within-subject trial, 18 men, 10 weeks | A lower load lifted to failure gave similar hypertrophy to a heavy load |

The papers form three real disagreement clusters: **training volume** (two positive results against one non-significant difference), **training frequency** (the same group's 2016 positive result against its 2019 null result when volume is equated), and **load** (heavier better against similar when taken to failure). Pairs across clusters concern different exposures and are labelled "different questions".

The main demo question targets the frequency cluster because its null result is stated unambiguously. Heaselgrave 2019 shows the system being conservative: its abstract reports no significant difference but also moderate-to-large effect sizes, so the verifier rates a "no effect" finding as only partly supported and excludes it.

A natural counterpoint, Barbalho et al. ("Evidence of a ceiling effect for training volume…"), was excluded because PubMed marks it as **retracted**. The system does not yet check for retractions automatically.

**Licensing.** No excerpt has a verified open licence, so every paper is abstract-only and the "fetch full text" action never applies to the bundled corpus. It is exercised by an automated test and by live discovery mode.

## Domain vocabulary

Topic-specific knowledge is data stored alongside the corpus, not code: demo questions, the extraction hint (the canonical names for outcomes, exposures, populations and designs), worked direction examples, keyword maps that turn free-text outcomes and exposures into canonical labels, and query synonyms used by keyword matching (for example *bigger* → *hypertrophy*, *sets* → *volume*). Pointing the system at a new topic means supplying a new corpus and vocabulary; the pipeline does not change.

## The article library

Every passage is converted into a **768-dimensional embedding vector** by the nomic-embed-text model, then normalized to unit length so that cosine similarity is a dot product. The model is asymmetric: stored passages are encoded with a "search document" prefix and queries with a "search query" prefix, as it was trained.

The vectors live in one persistent collection in **Chroma**, a vector database using cosine distance, in a single shared namespace called the library. Each entry carries metadata (paper, section, DOI, year, source URL) so queries can be filtered to specific papers. A copy of each passage and its vector is also kept in the relational database, which is what lets the system list and count indexed passages per article.

- **At server start**, any bundled passage not yet in the library is embedded and added.
- **During research**, runs search the library filtered to the papers they selected, and any passage a run fetches (for example from live discovery) is added to it.
- **Embeddings are cached** by model name and a hash of the text, so the same text is never embedded twice. Model *answers* are never cached.

The library is visible to users through the API (list, detail and search) and the Articles view of the interface. A user sees exactly the text the models read.

## Stage 1: paper discovery

Decides which papers a run considers.

1. The planner's first search term is embedded as a query.
2. Each candidate paper is represented by the embedding of its title and abstract. Optional publication-year filters are applied first.
3. Papers whose **cosine similarity is below 0.6 are discarded.** This threshold is what lets an off-topic question return no papers at all (the off-topic control scores at most 0.48).
4. The remaining papers are ranked by **cosine similarity + 0.5 × the fraction of query terms found in the title**, and the top *N* are kept (seven by default, three in the interface for speed).

The title bonus exists because seven papers on one topic have compressed similarity scores (0.80–0.86 for every paper on the demo questions); similarity alone ranked the wrong cluster first. Both the 0.6 threshold and the 0.5 weight were set by inspecting this corpus, not tuned on held-out data.

Query terms are lowercase alphanumeric tokens with stop-words removed and synonyms mapped through the domain vocabulary.

## Stage 2: passage retrieval

Decides exactly which text the models read.

1. Candidates are all library passages of the selected papers.
2. Each passage gets a hybrid score: **0.65 × semantic similarity + 0.25 × fraction of query terms in the passage + 0.10 × fraction of query terms in the paper's title.**
3. A **section bonus of +0.12** goes to methods, results and conclusions in the evidence-rich mode, or to abstract passages in the compact mode.
4. Passages are taken in score order until **12 passages** (the default top-K; 4 in compact mode) or a **6,000-token budget** is reached. Tokens are estimated at four characters each.

The hybrid score combines meaning (semantic similarity finds "twice a week" for a question about frequency) with exact terms (keyword overlap rewards precise scientific vocabulary).

## Live discovery (optional)

Instead of the bundled corpus, the system can search two scholarly APIs, OpenAlex and Europe PMC, through a separate configuration. Responses are size-limited and transient failures retried up to twice. A provider failure is recorded as a failure, never reported as "no papers exist". Abstracts are split into overlapping chunks of about 550 tokens with a 75-token overlap, broken at word boundaries, each with its character offsets, section and SHA-256 hash. Full text is fetched only where licensing permits. The bundled corpus remains the repeatable path for demonstrations and evaluation.
