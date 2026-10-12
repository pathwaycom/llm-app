#!/usr/bin/env python3
"""Render the published table and figures exclusively from saved measurements."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import statistics
from pathlib import Path

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


def embedder_breakdown(run, calibration):
    def private_total(stage):
        return sum(p['Private_Clean'] + p['Private_Dirty'] for p in calibration['stages'][stage]) / 1024
    baseline = private_total('baseline')
    worker_embedder_private = private_total('model_warm') - baseline
    processes = run['summary']['peak_processes']
    if not all('mapping_groups' in p for p in processes):
        raise ValueError('10 GB peak must include embedding-library mapping measurements')
    c = run['peak_components']
    # Initialization and live batches have different buffer lifetimes. Never
    # attribute more private memory than the measured worker footprint minus
    # its independently measured pre-embedder baseline. Supervisor private
    # pages remain in the residual; some may also be removable with a remote
    # embedder, so this estimate does not subtract them speculatively.
    embedding_private = min(worker_embedder_private, c['workers_private_mb'] - baseline)
    embedding_shared = sum(max(0, p['mapping_groups']['embedding']['Pss'] -
        p['mapping_groups']['embedding']['private_kb']) for p in processes) / 1024
    shared_increment = (sum(p['embedding_shared_kb'] for p in calibration['stages']['model_warm']) -
                        sum(p['embedding_shared_kb'] for p in calibration['stages']['baseline'])) / 1024
    embedding_shared = min(embedding_shared, max(0, shared_increment))
    metadata = c['connector_extra_mb_estimate']
    remaining_private = c['workers_private_mb'] + c['supervisors_private_mb'] - embedding_private
    other_shared = c['shared_pss_mb'] - embedding_shared
    if min(embedding_private, remaining_private, other_shared) < -1:
        raise ValueError('Embedder attribution is incompatible with measured peak pages')
    return {'local_embedder_private_mb_estimate': embedding_private,
            'local_embedder_shared_libraries_mb': embedding_shared,
            'file_watch_mb_estimate': metadata,
            'remaining_indexer_private_mb_estimate': remaining_private,
            'other_shared_mb': max(0, other_shared)}


def load(results):
    runs = []
    for size, label in SIZES:
        summary = json.loads((results / f"{size}-summary.json").read_text())
        with (results / f"{size}-memory.csv").open() as fh:
            samples = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(fh)]
        peak = max(s["pss_mb"] for s in samples)
        if abs(peak - summary["peak_pss_mb"]) > 0.11:
            raise ValueError(f"{size}: CSV peak does not match summary")
        if int(samples[-1]["chunks"]) != summary["max_observed_chunks"]:
            raise ValueError(f"{size}: CSV high-water chunk count does not match summary")
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
    lines = ["| corpus target | ≈ pages | files | chunks | indexing time | peak memory (PSS, GiB) | in Qdrant (GiB) |",
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
    ten = next(r for r in runs if r["size"] == "10gb")
    calibration = json.loads((args.results / 'embedder-calibration.json').read_text())
    if (calibration['image'] != environment['image'] or calibration['workers'] != 8
            or calibration['jemalloc_conf'] != 'background_thread:true'
            or calibration['omp_threads'] != '12' or 'baseline_includes' not in calibration):
        raise ValueError('Embedder diagnostic and indexing runs have different setups')
    c = embedder_breakdown(ten, calibration)
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
    fig, (ax, right) = plt.subplots(1, 2, figsize=(13.5, 4.8))
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
        dy = {'100mb': -16, '1gb': 0, '3gb': 12}.get(run['size'], 0)
        right.annotate(run["label"], (xx, yy), xytext=(5, dy), textcoords="offset points", fontsize=9)
    right.set(title="File-watch memory proxy", xlabel="watched files, thousands", ylabel="extra private memory, MiB")
    right.legend(fontsize=8)
    for axes in (ax, right):
        axes.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(args.assets / "bench-memory.png", dpi=130)
    plt.close(fig)

    derived['10gb_embedder_breakdown'] = c
    derived['10gb_indexer_without_local_embedder_mb_estimate'] = (
        ten['summary']['peak_pss_mb'] - c['local_embedder_private_mb_estimate'] - c['local_embedder_shared_libraries_mb'])
    (args.results / "derived.json").write_text(json.dumps(derived, indent=2) + "\n")
    values = list(c.values())
    labels = ["Local embedder: private memory\n(calibrated estimate)",
              "Local embedder: shared libraries\n(measured PSS)",
              "File-watch memory\n(rank-0 excess estimate)",
              "Indexer: engine, buffers, supervisors\n(private memory; estimate)",
              "Other shared pages\n(measured PSS)"]
    labels = [f"{label}\n{value / 1024:.2f} GiB" for label, value in zip(labels, values)]
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    wedges, _, _ = ax.pie(values, autopct=lambda p: f'{p:.0f}%' if p >= 6 else '',
           startangle=90, colors=["#5145ef", "#a5b4fc", "#10a34a", "#64748b", "#cbd5e1"],
           wedgeprops={"edgecolor": "white"})
    # Space callouts independently of tiny wedge angles, so shared-page and
    # metadata labels remain readable without overlapping.
    anchors = [(np.cos(np.deg2rad((w.theta1 + w.theta2) / 2)),
                np.sin(np.deg2rad((w.theta1 + w.theta2) / 2))) for w in wedges]
    for side in [-1, 1]:
        indexes = sorted([i for i, (x, y) in enumerate(anchors) if (1 if x >= 0 else -1) == side],
                         key=lambda i: anchors[i][1])
        positions = np.linspace(-1.0, 1.0, len(indexes)) if len(indexes) > 1 else [0]
        for index, y in zip(indexes, positions):
            ax.annotate(labels[index], xy=anchors[index], xytext=(side * 1.4, y),
                        ha='left' if side > 0 else 'right', va='center', fontsize=12,
                        arrowprops={'arrowstyle': '-', 'color': '#64748b',
                                    'connectionstyle': 'angle3,angleA=0,angleB=90'})
    ax.set_xlim(-1.85, 1.85)
    ax.set_title(f"10 GB corpus: measured peak {ten['summary']['peak_pss_mb'] / 1024:.1f} GiB PSS\n"
                 f"Estimated indexer without local embedder: {derived['10gb_indexer_without_local_embedder_mb_estimate'] / 1024:.1f} GiB")
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
The line is a least-squares fit with an intercept (~{slope:.0f} bytes per file;
fixed overhead estimate {intercept / 1024**2:.1f} MiB).
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
Shared embedding-library PSS comes directly from mapping samples
at the 10 GB peak, with other shared pages separated. Anonymous attribution
and the indexer-without-local-embedder figure are estimates, not an actual
external-service benchmark; client overhead and changes in working buffers
are not measured. The embedding service's own memory is outside that figure.
Derived values are saved in `derived.json`.

Regenerate with `python plot_results.py --update-readme`.
The script checks CSV peaks, chunk counts and process snapshots against summaries
and requires all six sizes before updating the publication.
"""
    (args.results / "README.md").write_text(notes)
    if args.update_readme:
        readme = REPO / "README.md"
        text = readme.read_text()
        start = text.index("| corpus", text.index("### Indexing resources"))
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
  <img src="https://raw.githubusercontent.com/pathwaycom/serviette/main/docs/assets/bench-memory-breakdown.png" alt="Breakdown at the 10 GB run's {ten['summary']['peak_pss_mb'] / 1024:.1f} GiB PSS peak: estimated local-embedder private memory, measured shared embedding libraries, estimated file-watch memory, remaining private memory and other shared pages." width="85%">
</p>
<p align="center"><em>Attribution at the actual 10 GB peak. Local-embedder private memory is estimated from a separate eight-process initialization diagnostic; shared library PSS is measured from mappings. Without the local embedder the indexer's footprint is estimated at {derived['10gb_indexer_without_local_embedder_mb_estimate'] / 1024:.1f} GiB, excluding the embedding service itself. Shared pages are counted once through PSS.</em></p>

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
