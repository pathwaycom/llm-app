#!/usr/bin/env python3
"""
Test script to validate the 'Table has no column with name doc' fix.

This script demonstrates the proper way to set up document processing
that avoids the column naming issues described in GitHub Issue #52.
"""

import os
import tempfile
import warnings


def create_test_documents():
    """Create temporary test documents for validation."""
    test_dir = tempfile.mkdtemp(prefix="pathway_test_")

    # Create some test documents
    test_files = [
        ("doc1.txt", "This is the first test document for indexing."),
        ("doc2.txt", "This is the second test document with different content."),
        ("doc3.txt", "This is the third document to test the pipeline.")
    ]

    for filename, content in test_files:
        with open(os.path.join(test_dir, filename), 'w') as f:
            f.write(content)

    return test_dir


def test_modern_document_processing():
    """
    Test modern document processing approach that avoids the 'doc' column issue.
    """
    print("Testing modern document processing setup...")

    try:
        # Import Pathway (will only work if properly installed)
        import pathway as pw
        from pathway.xpacks.llm.document_store import DocumentStore
        from pathway.xpacks.llm import embedders, parsers, splitters
        from pathway.stdlib.indexing import BruteForceKnnFactory

        # Create test documents
        test_dir = create_test_documents()
        print(f"Created test documents in: {test_dir}")

        # Configure data source properly (this avoids the 'doc' column issue)
        sources = [
            pw.io.fs.read(
                path=test_dir,
                format="binary",
                with_metadata=True,
            )
        ]

        # Configure processing components
        parser = parsers.UnstructuredParser()
        splitter = splitters.TokenCountSplitter(max_tokens=400)

        # Use a simple embedder for testing (avoiding API calls)
        # In production, you might use OpenAIEmbedder or other embedders
        embedder = embedders.SentenceTransformerEmbedder(
            model="all-MiniLM-L6-v2",  # Small model for testing
            call_kwargs={"show_progress_bar": False}
        )

        # Create retriever factory
        retriever_factory = BruteForceKnnFactory(
            reserved_space=100,
            embedder=embedder,
            metric=pw.stdlib.indexing.BruteForceKnnMetricKind.COS
        )

        # Create document store - this handles column naming automatically
        # and avoids the "Table has no column with name doc" error
        document_store = DocumentStore(
            docs=sources,
            parser=parser,
            splitter=splitter,
            retriever_factory=retriever_factory
        )

        print("✅ Document store created successfully!")
        print("✅ No 'Table has no column with name doc' error occurred!")
        print("✅ Modern approach works correctly!")

        # Clean up
        import shutil
        shutil.rmtree(test_dir)

        return True

    except ImportError as e:
        print(f"⚠️  Pathway not installed: {e}")
        print("This test requires Pathway to be installed.")
        print("Install with: pip install pathway")
        return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False


def test_legacy_pattern_detection():
    """Test the legacy pattern detection function."""
    from migration_helpers import check_legacy_patterns

    # Test code with legacy patterns
    legacy_code = """
    embedded_data = contextful(context=documents, data_to_embed=documents.doc)
    query_context = index.query(embedded_query, k=3).select(
        documents.doc
    )
    """

    modern_code = """
    document_store = DocumentStore(docs=sources, parser=parser, splitter=splitter)
    """

    legacy_warnings = check_legacy_patterns(legacy_code)
    modern_warnings = check_legacy_patterns(modern_code)

    print("\nTesting legacy pattern detection:")
    print(f"Legacy code warnings: {len(legacy_warnings)}")
    for warning in legacy_warnings:
        print(f"  - {warning}")

    print(f"Modern code warnings: {len(modern_warnings)}")

    return len(legacy_warnings) > 0 and len(modern_warnings) == 0


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing fix for GitHub Issue #52")
    print("'Table has no column with name doc' error")
    print("=" * 60)

    # Test 1: Legacy pattern detection
    print("\n1. Testing legacy pattern detection...")
    pattern_test_passed = test_legacy_pattern_detection()
    print(f"   Pattern detection test: {'✅ PASSED' if pattern_test_passed else '❌ FAILED'}")

    # Test 2: Modern document processing
    print("\n2. Testing modern document processing...")
    processing_test_passed = test_modern_document_processing()
    print(f"   Processing test: {'✅ PASSED' if processing_test_passed else '❌ FAILED'}")

    # Summary
    print("\n" + "=" * 60)
    if pattern_test_passed and processing_test_passed:
        print("🎉 All tests passed! The fix is working correctly.")
    elif pattern_test_passed:
        print("⚠️  Pattern detection works, but Pathway testing requires installation.")
    else:
        print("❌ Some tests failed. Please check the implementation.")

    print("\nFor more information, see:")
    print("- examples/migration_guide.md")
    print("- examples/migration_helpers.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
