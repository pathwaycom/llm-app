"""Audit frozen input using the benchmark image's actual product splitter.

Run outside measured indexing. UTF8Parser decodes .txt bytes without alteration.
Each directory is a task; no embeddings or backend writes are involved.
"""
import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path


def initialize():
    global splitter
    from serviette.config import SplitterConfig
    from serviette.indexer.graph import build_xpack_splitter
    splitter = build_xpack_splitter(SplitterConfig(type="token_count", chunk_size=512))


def count_directory(directory):
    documents = chunks = corpus_bytes = 0
    for path in Path(directory).glob("*.txt"):
        payload = path.read_bytes()
        text = payload.decode("utf-8")
        documents += 1
        corpus_bytes += len(payload)
        chunks += len(splitter.chunk(text))
    return documents, chunks, corpus_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--sizes", nargs="+", default=["3gb", "10gb", "30gb"])
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    with mp.Pool(args.workers, initializer=initialize) as pool:
        for size in args.sizes:
            started = time.monotonic()
            directories = sorted((Path(args.data_root) / size / "docs").iterdir())
            totals = [0, 0, 0]
            for completed, counts in enumerate(pool.imap_unordered(count_directory, directories), 1):
                totals = [a + b for a, b in zip(totals, counts)]
                if completed % 20 == 0 or completed == len(directories):
                    print(f"{size}: directories {completed}/{len(directories)}, documents {totals[0]}, chunks {totals[1]}, elapsed {time.monotonic()-started:.0f}s", flush=True)
            result = dict(zip(["documents", "exact_chunks", "corpus_bytes"], totals))
            result.update(dataset=size, elapsed_seconds=round(time.monotonic()-started, 1),
                          source="Frozen corpus files; UTF-8 decode and actual build_xpack_splitter, token_count=512; executed in immutable serviette-bench image")
            (Path(args.results) / f"{size}-expected-output.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
