"""Fast check for the zero-cost guard (run: python tests_bench_guard.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_bench import _assert_zero_cost

root = Path(__file__).parent
_assert_zero_cost(root / "config.yaml")  # the real config must pass

bad = root / "results" / "_guard_check.yaml"
bad.parent.mkdir(exist_ok=True)
bad.write_text("embedder:\n  type: openai\n")
try:
    import shutil
    shutil.copy(root / "docker-compose.yml", bad.parent / "docker-compose.yml")
    _assert_zero_cost(bad)
except SystemExit as exc:
    assert "zero-cost guard" in str(exc)
    print("guard OK: real config passes, paid embedder rejected")
else:
    raise AssertionError("guard failed to reject a paid embedder")
finally:
    bad.unlink(missing_ok=True)
    (bad.parent / "docker-compose.yml").unlink(missing_ok=True)
