#!/usr/bin/env python3
"""Run the six published sizes sequentially, then render one consistent report."""
from __future__ import annotations

import datetime
import fcntl
import gzip
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SIZES = [("100mb", 100), ("1gb", 1000), ("3gb", 3000),
         ("10gb", 10000), ("30gb", 30000), ("50gb", 50000)]


def main():
    if not os.environ.get("PATHWAY_LICENSE_KEY"):
        raise SystemExit("PATHWAY_LICENSE_KEY must be set")
    if os.environ.get("BENCH_JEMALLOC_CONF") != "background_thread:true":
        raise SystemExit("Set BENCH_JEMALLOC_CONF=background_thread:true")
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    data_root = Path(os.environ["BENCH_DATA_ROOT"])
    data_root.mkdir(parents=True, exist_ok=True)
    with (results / ".rerun.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _run(results, data_root)


def _run(results, data_root):
    def output(cmd):
        return subprocess.check_output(cmd, text=True).strip()

    versions = output(["docker", "run", "--rm", "--entrypoint", "python",
                       "serviette-bench", "-c",
                       "import importlib.metadata as m,json; print(json.dumps({k:m.version(k) for k in ['serviette','pathway','torch','sentence-transformers','qdrant-client']}))"])
    metadata = {
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": output(["git", "rev-parse", "HEAD"]),
        "cpu": output(["lscpu"]), "logical_cpus": os.cpu_count(),
        "memory": Path("/proc/meminfo").read_text(), "kernel": platform.release(),
        "docker": output(["docker", "--version"]),
        "versions": json.loads(versions),
        "image": output(["docker", "image", "inspect", "serviette-bench", "--format", "{{.Id}}"]),
        "environment": {key: os.environ.get(key) for key in
                        ["BENCH_DATA_ROOT", "BENCH_JEMALLOC_CONF", "BENCH_OMP_THREADS", "COMPOSE_PROJECT_NAME"]},
    }
    (results / "run-environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for size, mb in SIZES:
        print(f"Preparing {size}", flush=True)
        dataset = data_root / size
        if not (dataset / "questions.json").exists():
            if (dataset / "docs").exists() and any((dataset / "docs").iterdir()):
                raise RuntimeError(f"Incomplete dataset at {dataset}; use a fresh BENCH_DATA_ROOT")
            subprocess.run([sys.executable, str(ROOT / "prepare_dataset.py"),
                            "--size-mb", str(mb), "--out", str(dataset)], check=True)
        if (dataset / 'preparation.json').exists():
            shutil.copy2(dataset / 'preparation.json', results / f'{size}-preparation.json')
        print(f"Indexing {size}", flush=True)
        # Count the actual frozen corpus, including its chosen byte boundary,
        # outside the measured run and using the same immutable product image.
        subprocess.run([
            "docker", "run", "--rm",
            "-e", "HF_HUB_OFFLINE=1", "-e", "OMP_NUM_THREADS=1",
            "-v", f"{data_root.resolve()}:/datasets:ro",
            "-v", f"{ROOT / 'count_expected_chunks.py'}:/bench/count_expected_chunks.py:ro",
            "-v", f"{results}:/results", metadata["image"],
            "python", "/bench/count_expected_chunks.py", "--data-root", "/datasets",
            "--results", "/results", "--sizes", size,
        ], check=True)
        expected = json.loads((results / f"{size}-expected-output.json").read_text())
        expected["image"] = metadata["image"]
        (results / f"{size}-expected-output.json").write_text(json.dumps(expected, indent=2) + "\n")
        try:
            subprocess.run([sys.executable, str(ROOT / "run_bench.py"), "--size", size,
                            "--expected-chunks", str(expected["exact_chunks"])], check=True)
        except BaseException:
            logs = subprocess.run(["docker", "compose", "logs", "--no-color"],
                                  cwd=ROOT, capture_output=True, text=True, check=False)
            with gzip.open(results / f"{size}-failure.txt.gz", "wt") as fh:
                fh.write(logs.stdout + logs.stderr)
            raise
        summary = json.loads((results / f"{size}-summary.json").read_text())
        if summary["chunks"] < summary["documents"]:
            raise RuntimeError(f"Incomplete indexing: {size}")
        print(f"Finished {size}: {summary['chunks']} chunks, {summary['peak_pss_mb']} MiB PSS", flush=True)
    print("Measuring local embedder initialization separately from indexing", flush=True)
    diagnostic = subprocess.run(
        ["docker", "compose", "run", "--rm", "--no-deps", "-T", "-v",
         f"{ROOT / 'measure_embedder.py'}:/bench/measure_embedder.py:ro",
         "indexer", "python", "/bench/measure_embedder.py"],
        cwd=ROOT, capture_output=True, text=True, check=True)
    calibration = json.loads(diagnostic.stdout)
    calibration["image"] = metadata["image"]
    (results / "embedder-calibration.json").write_text(json.dumps(calibration, indent=2) + "\n")
    with gzip.open(results / "embedder-calibration.txt.gz", "wt") as fh:
        fh.write(diagnostic.stderr)
    subprocess.run([sys.executable, str(ROOT / "plot_results.py"), "--update-readme"], check=True)
    print("All six sizes measured; README and figures regenerated.", flush=True)


if __name__ == "__main__":
    main()
