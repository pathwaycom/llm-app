# Real-time data indexing benchmark

Measures the two claims that matter for the serviette indexer:

1. **Indexing speed** — wall-clock time to index a document collection end to
   end (parse → chunk → embed → write to the vector DB).
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
  existing chunk-count and CPU-idleness checks in `run_bench.py`; indexing
  time is the time of the last observed chunk-count increase.
- **server** — `serviette server`; used after indexing to replay the accuracy
  questions through `/api/v1/retrieve`.

Memory is sampled every three seconds across the indexer container's
processes: RSS from `/proc/<pid>/status`, PSS and private-page counts from
`/proc/<pid>/smaps_rollup`. Peak PSS is the maximum sampled sum. Shared pages
are counted once through PSS. Summed `VmHWM` is retained in CSV as an upper
bound on RSS, since different processes can peak at different times.
Per-process samples include the Pathway worker rank, excluding the sampler.

The completion detector also requires successful parsing of every input
file. A chunk-rich subset can exceed the total file count and remain quiet
while the source is still being enumerated; this must not end sampling.
For a frozen corpus, `--expected-chunks N` additionally requires an exact
Qdrant count of N before accepting completion. This validates complete
output; the published approximate counter, 180-second quiet window,
30-core activity threshold and last-counter-increase time formula remain
the same. The excluded early 50 GB measurements are retained under
`results/diagnostics/50gb-premature-completion/`.

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
and compressed indexer logs.

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

`plot_results.py` reads all six CSVs and summaries, validates their agreement,
and generates both README images and the table. It also saves `derived.json`
with the fitted file-watch estimate and peak-memory ratio. The pie separates
estimated local-embedder private memory, measured shared embedding-library
PSS, estimated file-watch memory, remaining private memory and other shared
pages. It estimates what remains in the indexer with an external embedder,
excluding the embedding service itself. Anonymous-memory attribution uses
the separate diagnostic and remains an estimate; shared library pages come
from the main run's mappings.
See `results/README.md` for the recorded setup and attribution formula.
