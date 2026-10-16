"""Exercise publication orchestration without running the multi-hour workload."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import rerun_all


class RerunTests(unittest.TestCase):
    def test_reused_corpora_are_counted_before_indexing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            datasets = root / "datasets"
            for size, _ in rerun_all.SIZES:
                corpus = datasets / size
                corpus.mkdir(parents=True)
                (corpus / "questions.json").write_text("[]")
            calls = []

            def output(command, **kwargs):
                if "import importlib.metadata" in command[-1]:
                    return '{}'
                return "test-image"

            def run(command, **kwargs):
                calls.append(command)
                if "/bench/count_expected_chunks.py" in command:
                    size = command[-1]
                    (root / "results" / f"{size}-expected-output.json").write_text(
                        json.dumps({"documents": 2, "exact_chunks": 7}))
                elif str(root / "run_bench.py") in command:
                    size = command[command.index("--size") + 1]
                    self.assertEqual(command[-2:], ["--expected-chunks", "7"])
                    self.assertIn("image", json.loads(
                        (root / "results" / f"{size}-expected-output.json").read_text()))
                    (root / "results" / f"{size}-summary.json").write_text(
                        json.dumps({"chunks": 7, "documents": 2, "peak_pss_mb": 10}))
                return SimpleNamespace(stdout='{}', stderr='')

            with patch.object(rerun_all, "ROOT", root), patch.dict(os.environ, {
                "PATHWAY_LICENSE_KEY": "test", "BENCH_JEMALLOC_CONF": "background_thread:true",
                "BENCH_DATA_ROOT": str(datasets),
            }), patch.object(rerun_all.subprocess, "check_output", side_effect=output), \
                    patch.object(rerun_all.subprocess, "run", side_effect=run), \
                    contextlib.redirect_stdout(io.StringIO()):
                rerun_all.main()
            self.assertFalse(any(str(root / "prepare_dataset.py") in c for c in calls))
            self.assertEqual(sum('/bench/count_expected_chunks.py' in c for c in calls), 6)
            self.assertIn(str(root / "plot_results.py"), calls[-1])


if __name__ == "__main__":
    unittest.main()
