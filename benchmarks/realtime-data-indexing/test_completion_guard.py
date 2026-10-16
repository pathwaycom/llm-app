"""Regression checks for premature completion on chunk-rich input subsets."""
import unittest

from run_bench import _ParsingProgress, _ready_to_finish


class CompletionGuardTests(unittest.TestCase):
    def ready(self, **changes):
        values = {"documents": 17083603, "parsed_documents": 17083603,
                  "chunks": 37472786, "last_change": 100, "last_busy": 100,
                  "now": 281, "stats_available": True}
        values.update(changes)
        return _ready_to_finish(**values)

    def test_chunk_rich_subset_is_incomplete(self):
        self.assertFalse(self.ready(parsed_documents=13889356, chunks=31535316))

    def test_complete_quiet_output(self):
        self.assertTrue(self.ready())

    def test_unavailable_stats_and_recent_activity(self):
        self.assertFalse(self.ready(stats_available=False))
        self.assertFalse(self.ready(last_busy=200))
        self.assertFalse(self.ready(last_change=200))

    def test_parsing_progress(self):
        progress = _ParsingProgress("unused")
        progress._observe(b"INFO:serviette.indexer.graph:parsing doc (1 KB)")
        self.assertEqual(progress.parsed_documents, 0)
        progress._observe(b"INFO:serviette.indexer.graph:parsed doc: 1000 chars in 0.0s")
        self.assertEqual(progress.parsed_documents, 1)
        self.assertGreater(progress.last_change, 0)
        progress._observe(b"ERROR:document is indexed as EMPTY")
        self.assertEqual(progress.failed_documents, 1)


if __name__ == "__main__":
    unittest.main()
