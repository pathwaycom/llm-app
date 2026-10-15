# Indexing benchmark results

Measured from 2026-10-12T19:00:22.529304+00:00, on 96 logical CPUs.
Exact CPU description, RAM, kernel, image ID and installed package versions:
`run-environment.json`. Resolved compose configurations redact the license key.
The workload, 180-second quiet window, 30-core activity threshold and
last-counter-increase time formula are retained. Completion also requires
all input files to be parsed; the repeated 50 GB run verifies its exact
output against the frozen-corpus count. Earlier measurements that stopped
prematurely are preserved under `diagnostics/50gb-premature-completion/`
and excluded. Independent splitter counts confirm complete output for
the other five sizes.

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
`50gb-preparation.json` and `50gb-preparation-full-target.json` record both
boundaries. The earlier five-language run stopped at 45,323.8 MiB; it is
preserved in `diagnostics/50gb-insufficient-corpus/` and excluded from this
publication and direct performance comparisons.

Peaks are the maximum sampled total PSS, not kernel high-water marks.
Sampling continues through the existing completion window.
The chunk-count methodology is unchanged: the summary uses Qdrant's
approximate count at completion, while CSV `chunks` retains the maximum
observed count used by the completion detector. Segment optimization can
reduce approximate counts, so these two fields need not be identical;
`max_observed_chunks` records the CSV's value in the summary explicitly.

`*-memory.csv` and `*-processes.jsonl.gz` record aggregate and per-process
measurements at the same times; `*-summary.json` includes the process snapshot
at peak PSS. `*-indexer.txt.gz` contains the container log.

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
Run `python verify_results.py` after regeneration to audit every process sample,
all published tables and the pie sum; `consistency-check.json` records the
result and hashes of both published figures.
