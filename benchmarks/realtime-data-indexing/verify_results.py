"""Audit published tables against every saved memory/process sample."""
import csv
import gzip
import hashlib
import json

from plot_results import REPO, ROOT, SIZES, load, table


def verify():
    results = ROOT / "results"
    runs = load(results)
    published = table(runs)
    for path in [REPO / "README.md", results / "README.md", results / "table.md"]:
        assert published in path.read_text(), f"Different table in {path}"
    audited = []
    for run in runs:
        size, summary = run["size"], run["summary"]
        with (results / f"{size}-memory.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        previous_time = previous_chunks = -1
        last_increase = peak = 0
        peak_time = 0
        with gzip.open(results / f"{size}-processes.jsonl.gz", "rt") as stream:
            count = 0
            for row in rows:
                line = stream.readline()
                assert line, f"{size}: missing process sample"
                sample = json.loads(line)
                elapsed, chunks = float(row["elapsed_s"]), int(row["chunks"])
                assert elapsed > previous_time, f"{size}: nonmonotonic sample time"
                assert chunks >= previous_chunks, f"{size}: decreasing high-water count"
                assert abs(elapsed - sample["elapsed_s"]) <= 0.11
                for column, metric in [("pss_mb", "Pss"), ("rss_mb", "VmRSS")]:
                    measured = sum(p.get(metric, 0) for p in sample["processes"]) / 1024
                    assert abs(float(row[column]) - measured) <= 0.11, (size, column, elapsed)
                pss = sum(p.get("Pss", 0) for p in sample["processes"]) / 1024
                if pss > peak:
                    peak, peak_time = pss, elapsed
                if chunks > previous_chunks and chunks > 0:
                    last_increase = elapsed
                previous_time, previous_chunks = elapsed, chunks
                count += 1
            assert not stream.readline(), f"{size}: extra process samples"
        assert abs(peak - summary["peak_pss_mb"]) <= 0.11
        assert abs(peak_time - summary["peak_elapsed_s"]) <= 0.11
        assert abs(last_increase - summary["indexing_seconds"]) <= 0.11
        assert abs(sum(run["peak_components"].values()) - peak) <= 0.11
        assert (results / f"{size}-memory.png").is_file()
        audited.append({"size": size, "samples_checked": count,
                        "peak_pss_gib": summary["peak_pss_mb"] / 1024,
                        "last_chunk_increase_seconds": last_increase})
    expected = json.loads((results / "50gb-expected-output.json").read_text())
    backend = json.loads((results / "50gb-postrun-qdrant.json").read_text())
    assert backend["exact_count"]["result"]["count"] == expected["exact_chunks"]
    derived = json.loads((results / "derived.json").read_text())
    ten = next(r for r in runs if r["size"] == "10gb")["summary"]
    components = derived["10gb_embedder_breakdown"]
    assert abs(sum(components.values()) - ten["peak_pss_mb"]) <= 0.11
    remaining = (ten["peak_pss_mb"] - components["local_embedder_private_mb_estimate"]
                 - components["local_embedder_shared_libraries_mb"])
    assert remaining == derived["10gb_indexer_without_local_embedder_mb_estimate"]
    assert derived["peak_memory_ratio"] == runs[-1]["summary"]["peak_pss_mb"] / runs[0]["summary"]["peak_pss_mb"]
    assets = [REPO / "docs/assets" / name for name in ["bench-memory.png", "bench-memory-breakdown.png"]]
    readme = (REPO / "README.md").read_text()
    for path in assets:
        assert f'src="docs/assets/{path.name}"' in readme
    report = {"status": "passed", "sizes": len(SIZES), "runs": audited,
              "tables_identical": True, "all_process_samples_match_csv": True,
              "pie_components_match_measured_peak": True,
              "external_embedder_indexer_gib_estimate": remaining / 1024,
              "figure_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in assets}}
    (results / "consistency-check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    verify()
