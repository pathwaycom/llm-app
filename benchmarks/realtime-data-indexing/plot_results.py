#!/usr/bin/env python3
"""Render the published table and figures exclusively from saved measurements."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
SIZES = [("100mb", "100 MB"), ("1gb", "1 GB"), ("3gb", "3 GB"),
         ("10gb", "10 GB"), ("30gb", "30 GB"), ("50gb", "50 GB")]


def private_mb(process):
    return (process.get("Private_Clean", 0) + process.get("Private_Dirty", 0)) / 1024


def components(processes):
    """Measured private/shared pages; rank-0 excess is an attribution estimate.

    Rank 0 owns the filesystem connector. Its excess over the median private
    footprint of the other workers is a proxy, not an allocation profiler.
    Do not label the entire worker baseline as 'PyTorch': it also includes
    the engine and working buffers, which smaps cannot distinguish.
    """
    workers = [p for p in processes if p["worker_rank"] is not None]
    rank0 = [p for p in workers if p["worker_rank"] == 0]
    others = [p for p in workers if p["worker_rank"] != 0]
    if len(workers) != 8 or len(rank0) != 1 or len(others) != 7:
        raise ValueError("Expected exactly eight Pathway workers including rank 0")
    extra = max(0, private_mb(rank0[0]) - statistics.median(private_mb(p) for p in others))
    worker_private = sum(private_mb(p) for p in workers)
    supervisor_private = sum(private_mb(p) for p in processes if p["worker_rank"] is None)
    total = sum(p.get("Pss", 0) for p in processes) / 1024
    shared = total - worker_private - supervisor_private
    if shared < -0.01:
        raise ValueError("Private pages exceed total PSS")
    return {"workers_private_mb": worker_private - extra,
            "connector_extra_mb_estimate": extra,
            "supervisors_private_mb": supervisor_private,
            "shared_pss_mb": max(0, shared)}


def duration(seconds):
    if seconds < 60:
        return f"{seconds:.0f} s"
    if seconds < 3600:
        return f"{seconds / 60:.1f} min"
    return f"{seconds / 3600:.1f} h"


def load(results):
    runs = []
    for size, label in SIZES:
        summary = json.loads((results / f"{size}-summary.json").read_text())
        with (results / f"{size}-memory.csv").open() as fh:
            samples = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(fh)]
        peak = max(s["pss_mb"] for s in samples)
        if abs(peak - summary["peak_pss_mb"]) > 0.11:
            raise ValueError(f"{size}: CSV peak does not match summary")
        if int(samples[-1]["chunks"]) != summary["chunks"]:
            raise ValueError(f"{size}: final CSV chunk count does not match summary")
        if summary["jemalloc_conf"] != "background_thread:true" or summary["omp_threads"] != 12:
            raise ValueError(f"{size}: different measured configuration")
        with gzip.open(results / f"{size}-processes.jsonl.gz", "rt") as fh:
            last = None
            for line in fh:
                last = json.loads(line)
        if abs(last["elapsed_s"] - samples[-1]["elapsed_s"]) > 0.11:
            raise ValueError(f"{size}: process and aggregate series differ")
        if abs(sum(p.get("Pss", 0) for p in summary["peak_processes"]) / 1024 - peak) > 0.11:
            raise ValueError(f"{size}: peak process snapshot does not match total PSS")
        runs.append({"size": size, "label": label, "summary": summary,
                     "samples": samples, "final_components": components(last["processes"]),
                     "peak_components": components(summary["peak_processes"])})
    return runs


def table(runs):
    lines = ["| corpus | ≈ pages | files | chunks | indexing time | peak memory (PSS, GiB) | in Qdrant (GiB) |",
             "|---|---|---|---|---|---|---|"]
    for run in runs:
        s = run["summary"]
        ints = [f"{s[k]:,}".replace(",", " ") for k in ("approx_text_pages", "documents", "chunks")]
        lines.append(f"| {run['label']} | {' | '.join(ints)} | {duration(s['indexing_seconds'])} | {s['peak_pss_mb'] / 1024:.1f} | {s['vector_db_disk_mb'] / 1024:.1f} |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--assets", type=Path, default=REPO / "docs/assets")
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()
    runs = load(args.results)  # Fail before touching published files if any run is missing.
    environment = json.loads((args.results / "run-environment.json").read_text())
    files = np.array([r["summary"]["documents"] for r in runs], dtype=float)
    extra = np.array([r["final_components"]["connector_extra_mb_estimate"] for r in runs])
    # Allow fixed connector overhead rather than attributing it to file count.
    slope, intercept = np.polyfit(files, extra * 1024**2, 1)
    slope, intercept = float(slope), float(intercept)
    ratio = runs[-1]["summary"]["peak_pss_mb"] / runs[0]["summary"]["peak_pss_mb"]
    derived = {"connector_bytes_per_file_estimate": slope,
               "connector_fixed_overhead_bytes_estimate": intercept, "peak_memory_ratio": ratio,
               "runs": [{"size": r["size"], "peak_components": r["peak_components"],
                         "final_components": r["final_components"]} for r in runs]}
    (args.results / "derived.json").write_text(json.dumps(derived, indent=2) + "\n")
    args.assets.mkdir(parents=True, exist_ok=True)
    fig, (ax, right) = plt.subplots(1, 2, figsize=(15, 4.8))
    for run in runs:
        s = run["summary"]
        ax.plot([row["elapsed_s"] / 3600 for row in run["samples"]],
                [row["pss_mb"] / 1024 for row in run["samples"]],
                label=f"{run['label']} (peak {s['peak_pss_mb'] / 1024:.1f} GiB)")
    ax.set(title="Indexer PSS over time", xlabel="hours", ylabel="PSS, GiB", ylim=(0, None))
    ax.legend(fontsize=9)
    right.scatter(files / 1000, extra, color="#5145ef", label="rank-0 private-memory excess (estimate)")
    x = np.linspace(0, files.max() * 1.05, 100)
    right.plot(x / 1000, (intercept + slope * x) / 1024**2, "--", color="#10a34a", label=f"fit: fixed overhead + ~{slope:.0f} bytes × files")
    for run, xx, yy in zip(runs, files / 1000, extra):
        right.annotate(run["label"], (xx, yy), xytext=(5, 0), textcoords="offset points", fontsize=9)
    right.set(title="File-watch memory proxy", xlabel="watched files, thousands", ylabel="extra private memory, MiB")
    right.legend(fontsize=8)
    for axes in (ax, right):
        axes.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(args.assets / "bench-memory.png", dpi=130)
    plt.close(fig)

    ten = next(r for r in runs if r["size"] == "10gb")
    c = ten["peak_components"]
    values = list(c.values())
    labels = ["Worker private pages\n(embeddings + engine + buffers)",
              "Rank-0 excess\n(file-watch estimate)", "Supervisor private pages", "Shared pages (PSS)"]
    labels = [f"{label}\n{value / 1024:.2f} GiB" for label, value in zip(labels, values)]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.pie(values, labels=labels, autopct="%1.0f%%", colors=["#5145ef", "#10a34a", "#cbd5e1", "#a5b4fc"],
           wedgeprops={"edgecolor": "white"})
    ax.set_title(f"10 GB corpus: breakdown at measured peak ({ten['summary']['peak_pss_mb'] / 1024:.1f} GiB PSS)")
    fig.tight_layout()
    fig.savefig(args.assets / "bench-memory-breakdown.png", dpi=130)
    plt.close(fig)

    published_table = table(runs)
    (args.results / "table.md").write_text(published_table + "\n")
    notes = f"""# Indexing benchmark results

Measured from {environment['started_utc']}, on {environment['logical_cpus']} logical CPUs.
Exact CPU description, RAM, kernel, image ID and installed package versions:
`run-environment.json`. Resolved compose configurations redact the license key.
Indexing settings and completion criteria are unchanged from `run_bench.py`.

{published_table}

Input labels retain the published nominal sizes: 1 GB means a target of
1,000 MiB of text; 100 MB means 100 MiB. Memory and disk columns use GiB;
CSV columns ending in `_mb` contain MiB. Pages use 2,000 bytes per page.
Peaks are the maximum sampled total PSS, not kernel high-water marks.
Sampling continues through the existing completion window.

`*-memory.csv` and `*-processes.jsonl.gz` record aggregate and per-process
measurements at the same times; `*-summary.json` includes the process snapshot
at peak PSS. `*-indexer.txt.gz` contains the container log.

The right panel estimates file-watch memory as rank 0's private-page excess
over the median of the seven other workers at the final sample. It includes
any other unequal worker allocations; it is not an allocation-level measurement.
The line is a least-squares fit with an intercept (~{slope:.0f} bytes per file;
fixed overhead estimate {intercept / 1024**2:.1f} MiB).
The pie splits peak PSS into worker private pages, estimated rank-0 excess,
supervisor private pages and shared PSS. Worker pages include the engine,
embedding runtime and buffers; `/proc` cannot attribute them separately.
Derived values are saved in `derived.json`.

Regenerate with `python plot_results.py --update-readme`.
The script checks CSV peaks, chunk counts and process snapshots against summaries
and requires all six sizes before updating the publication.
"""
    (args.results / "README.md").write_text(notes)
    if args.update_readme:
        readme = REPO / "README.md"
        text = readme.read_text()
        start = text.index("| corpus |", text.index("### Indexing resources"))
        end = text.index("### Retrieval accuracy", start)
        versions = environment["versions"]
        replacement = f"""{published_table}

The table and both figures come from the same six runs. Raw summaries,
memory samples, per-process snapshots and resolved configurations are in
[results](benchmarks/realtime-data-indexing/results/README.md).
Memory and disk sizes use GiB; input labels are nominal targets
(1 GB = 1,000 MiB of extracted text). A page is approximately 2,000 bytes.

Documents flow through the pipeline rather than accumulating in it.
The file-watch index retains metadata per watched file to detect edits and
deletions, so its cost depends on file count. The right panel estimates this
cost from the connector worker's extra private memory: the fitted slope is
**~{slope:.0f} bytes per file**. This proxy also includes unequal worker
buffers; it does not isolate individual allocations.

The embedding runtime, engine and working buffers account for the worker
baseline. The curves show how total memory evolves during indexing,
including any steps as file-watch metadata and buffers grow.
Parsed-text cache, persistence snapshots and stored embeddings live on disk.
Across these runs a **500× larger input target costs {ratio:.1f}× the peak PSS**.

<p align="center">
  <img src="https://raw.githubusercontent.com/pathwaycom/serviette/main/docs/assets/bench-memory.png" alt="Measured indexer PSS over time for all six corpora; legends use the same peaks as the table. Right: estimated file-watch memory versus file count, fitted at approximately {slope:.0f} bytes per file." width="100%">
</p>
<p align="center"><em>All curves and table values come from the same runs with allocator background purging enabled. File-watch memory is estimated from rank-0 private-memory excess over the median of the other workers.</em></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pathwaycom/serviette/main/docs/assets/bench-memory-breakdown.png" alt="Breakdown at the 10 GB run's {ten['summary']['peak_pss_mb'] / 1024:.1f} GiB PSS peak: worker private pages, estimated file-watch excess, supervisor private pages and shared PSS." width="85%">
</p>
<p align="center"><em>Process measurements at the actual 10 GB peak. Worker private pages include embeddings, engine and buffers; the file-watch share is an estimate. Shared pages are counted once through PSS.</em></p>

Setup: {environment['logical_cpus']}-logical-CPU host (see the saved CPU model),
streaming mode, 8 worker processes with 12 OpenMP threads each,
local `static-retrieval-mrl-en-v1` embeddings, Matryoshka-truncated to 256 dims,
512-token chunks, Qdrant, and jemalloc `background_thread:true`.
No embedding API calls. Installed versions: serviette {versions['serviette']},
Pathway {versions['pathway']}, PyTorch {versions['torch']},
sentence-transformers {versions['sentence-transformers']}.
Peak memory is the maximum sampled PSS summed over the indexer container.
Indexing time uses the existing streaming completion criterion; see the
benchmark scripts and saved results for the full setup.

"""
        readme.write_text(text[:start] + replacement + text[end:])
    print(published_table)


if __name__ == "__main__":
    main()
