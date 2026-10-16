# Real-time data indexing benchmark

Measures two aspects of the serviette indexer:

1. **Indexing speed** — estimated wall-clock time for the indexing pipeline
   (parse → chunk → embed → write to the vector DB), using the approximate
   output-counter timing described below.
2. **Memory scaling** — document bytes flow through the pipeline, while
   file-watch metadata grows with the number of files. The output is a
   memory-over-time plot and sampled peak PSS (shared pages counted once).

Everything runs locally and costs nothing: embeddings are computed by a local
sentence-transformers model (`static-retrieval-mrl-en-v1`,
Matryoshka-truncated to 256 dims) — **no external API calls**.

## Setup

Three containers via docker-compose:

- **qdrant** — the vector store. Chosen deliberately: HNSW builds
  incrementally on upsert (fast indexing), it is designed for concurrent
  search-while-writing, and the Pathway sink keys points internally (no user
  primary key), so writes parallelize across Pathway workers.
- **indexer** — `serviette indexer` in streaming mode. Completion uses the
  chunk-count, parsing-progress and CPU-idleness checks in `run_bench.py`.
  Published indexing time ends at the last increase in the running maximum
  of Qdrant's approximate chunk count.
- **server** — `serviette server`; used after indexing to replay the accuracy
  questions through `/api/v1/retrieve`.

Memory sampling starts after server readiness, with a three-second sleep
between iterations; collecting memory and querying progress adds to that
interval. Samples cover the indexer container's processes: RSS from
`/proc/<pid>/status`, PSS and private-page counts from
`/proc/<pid>/smaps_rollup`. Peak PSS is the maximum sampled sum. Shared pages
are counted once through PSS. Summed `VmHWM` is retained in CSV as an upper
bound on RSS, since different processes can peak at different times.
Per-process samples include the Pathway worker rank, excluding the sampler.
Qdrant and API-server memory, unmapped filesystem cache and kernel memory
are outside this PSS measurement. It is not a RAM requirement for the whole
stack, and sampling can miss brief peaks.

The current completion detector also requires successful parsing of every input
file. A chunk-rich subset can exceed the total file count and remain quiet
while the source is still being enumerated; this must not end sampling.
For a frozen corpus, `--expected-chunks N` additionally requires an exact
Qdrant count of N before accepting completion. This validates complete
output; the published approximate counter, 180-second quiet window,
30-core activity threshold and last-counter-increase time formula remain
the same. The saved results distinguish the checks available for each run.

The timer starts before launching the indexer and server; dataset preparation,
model downloads and Qdrant startup are outside it. Approximate counts can
overshoot and later fall during segment optimization, so the last new maximum
need not coincide with the final write. An exact-count check validates output
completeness when performed, but does not change the published time estimate
or establish when the backend finished building its search index.

`count_expected_chunks.py` independently counts the frozen `.txt` inputs
using UTF-8 decoding and the product's configured 512-token splitter.
Run it in the same immutable benchmark image, outside measured indexing,
and save its `<size>-expected-output.json` files alongside the raw results.

## Dataset

`prepare_dataset.py` downloads Wikipedia parquet shards from Hugging Face
(public, fast CDN) and writes one `.txt` file per article until the target
size is reached. It also samples distinctive articles into `questions.json`;
each question must retrieve its own article (top-k accuracy sanity check).
Sources continue in this order: English, German, French, Spanish, Italian,
Portuguese, Dutch. The last two are needed to reach the published 50 GB
target. Preparation records actual bytes and file count in `preparation.json`
and fails if sources run out before the target; publication also checks the
measured corpus size.
The current product splitter merges trailing fragments shorter than 100
characters into the preceding chunk. Older published measurements used the
splitter without this merge, so old and new chunk counts, storage sizes and
timings do not isolate the effect of allocator tuning.

## Running

The serviette image is built from the repo checkout with the released
Pathway from PyPI (`docker compose build`, run automatically on first use);
`run_bench.py` pre-warms the local embedding-model cache, so the containers
themselves never touch the network.

```bash
python prepare_dataset.py --size-mb 100     # also: 1000, 3000, 10000
BENCH_JEMALLOC_CONF=background_thread:true python run_bench.py --size 100mb
```

Outputs land in `results/`: `<size>-memory.png` (memory over time),
`<size>-memory.csv`, `<size>-summary.json` (duration, MB/min, chunk count,
peak RSS/PSS, retrieval accuracy). Each run also saves per-process samples,
the process snapshot at peak PSS, a redacted resolved compose configuration,
and compressed indexer logs. CSV measurements, JSON results and the two
published figures in `docs/assets/` are committed. Raw `*.txt.gz` logs,
per-size `<size>-memory.png` plots, the generated `table.md` and the
`consistency-check.json` audit report stay local and are ignored by Git.

To regenerate the entire publication from a single series of runs:

```bash
export BENCH_DATA_ROOT=/path/on/a/large/disk/serviette-bench-datasets
export BENCH_JEMALLOC_CONF=background_thread:true
export BENCH_OMP_THREADS=12
export COMPOSE_PROJECT_NAME=serviette-consistency-bench
# PATHWAY_LICENSE_KEY must already be set. Build once for the full series.
docker compose build
python rerun_all.py
```

This runs 100mb → 1gb → 3gb → 10gb → 30gb → 50gb sequentially, records
an eight-process local-embedder initialization diagnostic, and then
calls `plot_results.py --update-readme`. Run it under nohup or tmux for the
multi-hour sizes. Datasets remain on the chosen disk after completion;
remove only this run's datasets when they are no longer needed.
Completed datasets (with `questions.json`) are reused, preserving historical
corpus boundaries. Missing datasets are prepared to the full nominal target;
nonempty incomplete datasets are rejected. Before each measured run, the driver
independently counts chunks in that corpus using the recorded image and passes
`--expected-chunks` to require an exact Qdrant count at completion. The audit
may download tokenizer data; it does not embed text or call an embedding API.
Reading the corpus for this audit can warm the filesystem cache. Containers
start with fresh database and persistence state, but the workflow does not
control the operating system's cache state or measure cold-cache I/O.

`plot_results.py` reads all six CSVs and summaries, validates their agreement,
and generates both README images and the table. It also saves `derived.json`
with the fitted file-watch estimate and peak-memory ratio. The pie separates
estimated local-embedder private memory, estimated shared embedding-library
PSS, estimated file-watch memory, remaining private memory and other shared
pages. It estimates what remains in the indexer with an external embedder,
excluding the embedding service itself. Anonymous-memory attribution uses
the separate diagnostic and remains an estimate; shared library pages come
from the main run's mappings.
See `results/README.md` for the recorded setup and attribution formula.

The publication contains one final run per corpus size, with no estimate of
run-to-run variability. Its memory scaling describes this configuration and
these corpora; file count and text volume both change between sizes. The
saved image IDs and package versions identify the measured environment, but
the build recipe uses floating image tags and dependency versions, and model
and dataset downloads have no pinned revision. A future rebuild can therefore
use a different environment or inputs.

Run `python verify_results.py` directly from a checkout to independently check
every aggregate sample against its per-process snapshot, recompute peaks
and indexing times, compare all published tables, and verify the pie sum
and complete 50 GB output. No benchmark rerun or plot regeneration is needed.
The command prints its report and writes a local `results/consistency-check.json`
with the checks and hashes of both published figures. `plot_results.py` can
regenerate the per-size plots and standalone table from the saved measurements.
