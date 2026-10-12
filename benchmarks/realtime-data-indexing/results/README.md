# Indexing benchmark rerun — in progress

Started 2026-10-12. All six sizes run sequentially with the published
configuration: streaming, eight workers, 12 OpenMP threads per worker,
local static embeddings truncated to 256 dimensions, 512-token chunks,
Qdrant and jemalloc background purging. Exact host and package versions
are recorded in `run-environment.json`. Resolved compose files redact secrets.

Completed:

| corpus | files | chunks | indexing time | peak PSS (GiB) | Qdrant disk (GiB) | retrieval |
|---|---|---|---|---|---|---|
| 100 MB | 12 969 | 53 651 | 44.0 s | 6.86 | 0.61 | 5/5 |

The old 100 MB row reported 66,136 chunks, 39 s, 6.6 GB peak PSS and
0.6 GB Qdrant storage. The file count is unchanged. The entire corpus was
also split offline using stock `TokenCountSplitter(max_tokens=512)`:
66,136 chunks, of which 12,485 are trailing fragments below 100 characters
with a preceding chunk. The current serviette splitter merges those tails;
66,136 − 12,485 = 53,651 exactly. Saved as `100mb-splitter-comparison.json`.
This is a product change introduced in commit `3750fef`, not a benchmark
configuration change. No source documents are missing.

Each completed size saves aggregate CSV, summary JSON, per-size PSS PNG,
compressed per-process JSONL, redacted compose JSON and compressed indexer
logs. The CSV is written during execution. Peak PSS is the maximum sampled
container sum; data collection continues during the existing completion
window. `_mb` fields contain MiB. Input targets are nominally labeled:
100 MB means 100 MiB and 1 GB means 1,000 MiB of text.

The publication will be regenerated only after all six sizes complete and
the plotting script validates the summaries against their CSVs and process
snapshots. Its final result notes will replace this progress page.
