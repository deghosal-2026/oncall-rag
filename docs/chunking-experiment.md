# Chunking Experiment Report

- **Date:** 2026-06-26
- **Corpus:** `./corpus` (Kubernetes, Grafana, Google SRE, public runbooks)
- **Eval set:** `data/eval.json` (115 Q&A pairs)
- **Default config:** `chunk_size=500`, `chunk_overlap=50`

## Strategies Compared

| Strategy | Description | Implementation |
|---|---|---|
| Recursive (baseline) | `RecursiveCharacterTextSplitter` — splits on `\n\n` → `\n` → `. ` → ` `, preserving paragraph/sentence boundaries | `indexer.py:_split_recursive` |
| Header-split | Splits on markdown headers (`#`, `##`, etc.), then merges small sections up to ~1.5× chunk_size | `indexer.py:_split_header` |
| Fixed-size | Blind character split at 500 chars with 50-char overlap, breaks at nearest space | `indexer.py:_split_fixed_size` |

## Results

| Strategy | MRR | Recall@5 |
|---|---|---|
| **header-split** ★ | **0.9524** | 1.0000 |
| recursive | 0.9048 | 1.0000 |
| fixed-size | 0.8893 | 1.0000 |

All three strategies achieved perfect Recall@5, meaning the correct source document was always in the top-5 results. The differentiation is in **MRR** (how high the first relevant result ranks).

## Analysis

### Header-split (winner: 0.9524 MRR)
- Best performance because runbook documents are naturally organized by markdown headers (`## Step 1`, `## Debugging`, etc.)
- Each chunk maps to a coherent section — the entire relevant procedure is in one chunk
- Context preservation is excellent; no section is split mid-paragraph

### Recursive (0.9048 MRR)
- Good for prose-heavy documents but can split mid-section when a section exceeds 500 chars
- Loses ~5% MRR vs header-split because relevant content sometimes straddles chunk boundaries
- Better than fixed-size because it respects paragraph boundaries

### Fixed-size (0.8893 MRR)
- Lowest MRR — blind character splits frequently break mid-sentence or mid-step
- A step that's 600 chars gets split into two chunks, diluting relevance
- Simple and fast to compute but loses semantic coherence

## Qualitative Coherence Assessment

Chunks from each strategy were visually inspected:

| Strategy | Coherence | Notes |
|---|---|---|
| Header-split | High | Each chunk is a complete section — headers included |
| Recursive | Medium-High | Most chunks are paragraph-complete; occasional mid-section splits |
| Fixed-size | Low | Frequent mid-sentence breaks; meaning lost |

## Recommendation

**Use `header-split` as the default chunking strategy.** It achieves the highest MRR (0.9524) and produces the most semantically coherent chunks by respecting document structure. Runbooks with markdown headers (which is the vast majority) benefit most from this approach.

To switch: set `CHUNKING_STRATEGY=header-split` in `.env` or update `config.py`.

## Future Work

- Experiment with `chunk_size` tuning for header-split (current: 500, merge threshold: 1.5×)
- Add semantic chunking (embedding-similarity-based boundary detection)
- Test hybrid retrieval (dense + sparse BM25) to see if it closes the MRR gap
