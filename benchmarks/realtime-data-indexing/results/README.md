# Indexing benchmark results

Measured from 2026-10-12T19:00:22.529304+00:00, on 96 logical CPUs.
Exact CPU description, RAM, kernel, image ID and installed package versions:
`run-environment.json`. Resolved compose configurations redact the license key.
The workload, 180-second quiet window, 30-core activity threshold and
approximate-counter timing formula are retained. The current completion
detector also requires all input files to be parsed and, when an expected
count is supplied, verifies the exact output count. Independent splitter
counts match the saved final counts for all six sizes. The saved 50 GB run
additionally records complete parsing progress and an exact Qdrant count;
the five smaller runs record approximate backend counts.
The separate 50 GB audit scanned 17,083,603 frozen input files (52,428,765,709
bytes) in the original immutable benchmark image and produced exactly
37,472,786 chunks, matching the saved run and exact Qdrant count.
It ran outside the measured indexing workload; memory and timing results
are unchanged. `50gb-expected-output.json` records this independent audit.

| corpus target | ≈ pages | files | chunks (approx.) | indexing time | peak memory (PSS, GiB) | in Qdrant (GiB) |
|---|---|---|---|---|---|---|
| 100 MB | 52 431 | 12 969 | 53 651 | 44 s | 6.86 | 0.61 |
| 1 GB | 524 288 | 240 516 | 604 299 | 4.9 min | 6.82 | 1.85 |
| 3 GB | 1 572 864 | 841 890 | 1 888 846 | 15.4 min | 7.18 | 4.89 |
| 10 GB | 5 242 884 | 3 423 359 | 6 761 214 | 1.0 h | 8.16 | 16.07 |
| 30 GB | 15 728 646 | 9 202 620 | 20 933 962 | 3.1 h | 10.40 | 48.57 |
| 50 GB | 26 214 382 | 17 083 603 | 37 472 786 | 6.0 h | 14.65 | 84.45 |

Input labels retain the published nominal sizes: 1 GB means a target of
1,000 MiB of text; 100 MB means 100 MiB. Memory and disk columns use GiB;
CSV columns ending in `_mb` contain MiB. Pages use 2,000 bytes per page.
The 50 GB input restores the historical Portuguese/Dutch continuation and
matches the archived file count and approximate page count. Strictly filling
the nominal byte target adds 20 trailing Dutch articles (35,697 bytes);
these are preserved outside the input to reproduce the published cutoff.
`50gb-preparation.json` records the final boundary and the trimmed bytes
and document count.

Peaks are the maximum sampled total PSS, not kernel high-water marks.
Sampling continues through the existing completion window.
Only indexer processes are included: Qdrant and API-server memory, unmapped
filesystem cache and kernel memory are outside this measurement. It is not
a RAM requirement for the whole stack. Sampling starts after server readiness;
each iteration includes a three-second sleep plus collection and polling
overhead, so brief peaks may be missed.
The chunk-count methodology is unchanged: the summary uses Qdrant's
approximate count at completion, while CSV `chunks` retains the maximum
observed count used by the completion detector. Segment optimization can
reduce approximate counts, so these two fields need not be identical;
`max_observed_chunks` records the CSV's value in the summary explicitly.

Published indexing time is an estimate: elapsed time from before launching
the indexer and server to the last increase in the running maximum of the
approximate chunk count. Preparation, model downloads and Qdrant startup are
outside this interval. A temporary overcount can make the last new maximum
precede the final write. Checking the exact output count at completion does
not revise that timestamp or measure when the backend's search index is ready.
The saved timing values retain this definition.

`*-memory.csv` and `*-processes.jsonl.gz` record aggregate and per-process
measurements at the same times; `*-summary.json` includes the process snapshot
at peak PSS. `*-indexer.txt.gz` contains the local container log and is
excluded from Git. Measurements, derived values, this report and the two
published figures in `docs/assets/` are committed. Per-size `*-memory.png`
plots, the standalone `table.md` and `consistency-check.json` stay local and
are ignored by Git; they can be regenerated from the saved measurements.

One final run per corpus size is published, without an estimate of run-to-run
variability. File count and text volume both change across sizes, so these
measurements do not establish constant memory at a fixed file count. They
describe this local static-embedding model, plain-text workload and configuration.
The product splitter merges trailing fragments shorter than 100 characters
into the preceding chunk; older published measurements predate that behavior.
Differences in chunk counts, disk usage and timing therefore cannot be
attributed to allocator tuning alone.

The saved runs do not establish a controlled cold-cache result. Fresh database
and persistence state do not imply a cold operating-system cache. The current
rerun driver reads the entire corpus to count expected chunks before indexing,
which can warm that cache. Saved image IDs and key package versions identify
the measured environment; the build recipe still uses floating image tags
and dependency versions, and model and dataset downloads have no pinned
revision. A future rebuild can use different software or inputs.

The right panel estimates file-watch memory as rank 0's private-page excess
over the median of the seven other workers at the final sample. It includes
any other unequal worker allocations; it is not an allocation-level measurement.
The line is a least-squares fit with an intercept (~361 bytes per file;
fixed overhead estimate 45.9 MiB).
The pie attributes local-embedding private memory using an eight-process
controlled diagnostic in the same image: graph imports before the embedder,
UTF-8 parser and configured splitter initialized and warmed, embedding
runtime imported, model loaded and warmed on three 2,048-text batches, then
model released. `embedder-calibration.json` records all stages. The private
increment after warming estimates the local stack's private cost across eight
workers. This is capped at the observed non-file-watch worker private memory
minus the calibrated pre-embedder baseline, since live and diagnostic buffers
have different lifetimes. Supervisor private pages are left in the residual;
any embedding allocations there are not subtracted speculatively.
Shared embedding-library PSS starts from mapping samples at the 10 GB peak
and is capped by the diagnostic's shared-library increment, so libraries
already needed by the parser are retained in the residual. Other shared
pages are separated. Anonymous attribution
and the indexer-without-local-embedder figure are estimates, not an actual
external-service benchmark; client overhead and changes in working buffers
are not measured. The embedding service's own memory is outside that figure.
Derived values are saved in `derived.json`.

Regenerate with `python plot_results.py --update-readme`.
The script checks CSV peaks, chunk counts and process snapshots against summaries
and requires all six sizes before updating the publication.
Run `python verify_results.py` directly from a checkout to audit every process
sample, both published tables and the pie sum. It does not require a benchmark
rerun or regenerated per-size plots. It prints the result and writes a local
`consistency-check.json` with hashes of both published figures.
