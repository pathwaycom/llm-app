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
| 1 GB | 240 516 | 604 299 | 293.6 s | 6.82 | 1.85 | 18/20 |
| 3 GB | 841 890 | 1 888 846 | 921.9 s | 7.18 | 4.89 | 17/20 |
| 10 GB | 3 423 359 | 6 761 214 | 3620.7 s | 8.16 | 16.07 | 17/20 |
| 30 GB | 9 202 620 | 20 933 962 | 11028.8 s | 10.40 | 48.57 | 14/20 |

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

Qdrant approximate counts can fall during segment optimization. CSV `chunks`
records the completion detector's maximum observed count, and summary
`max_observed_chunks` preserves it explicitly; summary `chunks` is the
approximate count at completion. On 1 GB these are 604,598 and 604,299.
These fields retain the existing benchmark methodology, and are not exact
allocation or point-count audits.

The local-embedder diagnostic (`embedder-calibration.json`) separately runs
eight workers in the same image/environment. The baseline includes warmed
UTF-8 parsing and the configured splitter, which remain necessary with a
remote embedder. Measurements were taken between the 30 GB and 50 GB sizes.
The diagnostic's private-page increment is 5.17 GiB. Attribution at the
actual 10 GB peak caps it at observed worker memory minus that baseline:
4.60 GiB private embedding memory plus 0.28 GiB shared library PSS.
The remaining indexer footprint is estimated at 3.27 GiB, excluding an
external embedding service and unmeasured client/buffer changes. Other
shared pages remain in the residual. The saved `10gb-breakdown.json` and
`10gb-memory-breakdown.png` use the same measured 8.16 GiB peak; attribution
is an estimate rather than an external-service benchmark.
