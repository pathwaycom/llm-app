"""
Utility script to help users avoid the "Table has no column with name doc" error.

This script provides helper functions to validate data structure and provide
guidance on proper data formatting for Pathway LLM applications.

Addresses GitHub Issue #52: https://github.com/pathwaycom/llm-app/issues/52
"""

import pathway as pw
import warnings
from typing import List, Dict, Any, Optional


def validate_data_source(table: pw.Table, expected_format: str = "binary") -> Dict[str, Any]:
    """
    Validate that a data source is properly formatted for LLM processing.

    Args:
        table: Pathway table to validate
        expected_format: Expected data format (default: "binary")

    Returns:
        Dict containing validation results and recommendations
    """
    validation_result = {
        "is_valid": True,
        "warnings": [],
        "errors": [],
        "recommendations": []
    }

    # Check if table has the expected structure for document processing
    try:
        # Check for common column patterns
        column_names = [col for col in dir(table) if not col.startswith('_')]

        # For binary format, we expect 'data' column
        if expected_format == "binary":
            if 'data' not in column_names:
                validation_result["warnings"].append(
                    "No 'data' column found. For binary document processing, "
                    "ensure your data source uses format='binary'."
                )
                validation_result["recommendations"].append(
                    "Use pw.io.fs.read(path='...', format='binary', with_metadata=True)"
                )

        # Check for legacy 'doc' column expectation
        if 'doc' in column_names:
            validation_result["warnings"].append(
                "Found 'doc' column. This might be from legacy code. "
                "Modern Pathway LLM apps handle column naming automatically."
            )
            validation_result["recommendations"].append(
                "Consider using DocumentStore or VectorStoreServer for automatic handling."
            )

    except Exception as e:
        validation_result["errors"].append(f"Error during validation: {str(e)}")
        validation_result["is_valid"] = False

    return validation_result


def create_document_source(path: str,
                         format: str = "binary",
                         with_metadata: bool = True,
                         file_patterns: Optional[List[str]] = None) -> pw.Table:
    """
    Create a properly formatted document source for LLM processing.

    Args:
        path: Path to documents
        format: Data format (default: "binary")
        with_metadata: Whether to include metadata
        file_patterns: Optional file patterns to match

    Returns:
        Properly configured Pathway table
    """
    try:
        if file_patterns:
            # Handle multiple file patterns
            sources = []
            for pattern in file_patterns:
                source = pw.io.fs.read(
                    path=f"{path}/{pattern}",
                    format=format,
                    with_metadata=with_metadata
                )
                sources.append(source)
            # Combine multiple sources
            return pw.Table.concat(*sources) if len(sources) > 1 else sources[0]
        else:
            return pw.io.fs.read(
                path=path,
                format=format,
                with_metadata=with_metadata
            )
    except Exception as e:
        raise ValueError(f"Failed to create document source: {str(e)}")


def show_migration_guidance():
    """
    Display guidance for migrating from legacy code that expected 'doc' column.
    """
    print("=== Migration Guide: Fixing 'Table has no column with name doc' Error ===")
    print()
    print("ISSUE: Legacy code expected a 'doc' column that may not exist in your data.")
    print()
    print("SOLUTION: Use modern Pathway LLM abstractions that handle column naming automatically:")
    print()
    print("1. DocumentStore (Recommended):")
    print("   from pathway.xpacks.llm.document_store import DocumentStore")
    print("   document_store = DocumentStore(docs=sources, parser=parser, splitter=splitter)")
    print()
    print("2. VectorStoreServer (Alternative):")
    print("   from pathway.xpacks.llm.vector_store import VectorStoreServer")
    print("   vector_server = VectorStoreServer(*sources, embedder=embedder, parser=parser)")
    print()
    print("3. Proper Data Source Configuration:")
    print("   sources = pw.io.fs.read(path='./data', format='binary', with_metadata=True)")
    print()
    print("For more details, see: examples/migration_guide.md")
    print("="*70)


def check_legacy_patterns(code_string: str) -> List[str]:
    """
    Check code string for legacy patterns that might cause the 'doc' column error.

    Args:
        code_string: String containing code to check

    Returns:
        List of warnings about potential issues
    """
    warnings_found = []

    legacy_patterns = [
        ("documents.doc", "Direct access to 'doc' column - use DocumentStore instead"),
        ("data_to_embed=documents.doc", "Legacy embedding pattern - use modern embedders"),
        ("contextful(", "Legacy contextful function - use VectorStoreServer"),
        ("embedded_data = contextful", "Legacy embedding code - use DocumentStore"),
    ]

    for pattern, warning in legacy_patterns:
        if pattern in code_string:
            warnings_found.append(f"Found '{pattern}': {warning}")

    return warnings_found


# Example usage functions
def example_modern_setup():
    """
    Example of modern setup that avoids the 'doc' column issue.
    """
    print("=== Example: Modern Document Processing Setup ===")
    print()
    print("```python")
    print("import pathway as pw")
    print("from pathway.xpacks.llm.document_store import DocumentStore")
    print("from pathway.xpacks.llm import embedders, parsers, splitters")
    print("from pathway.stdlib.indexing import BruteForceKnnFactory")
    print()
    print("# Properly configured data source")
    print("sources = [")
    print("    pw.io.fs.read(")
    print("        path='./documents',")
    print("        format='binary',")
    print("        with_metadata=True")
    print("    )")
    print("]")
    print()
    print("# Configure processing components")
    print("parser = parsers.UnstructuredParser()")
    print("splitter = splitters.TokenCountSplitter(max_tokens=400)")
    print("embedder = embedders.OpenAIEmbedder()")
    print()
    print("# Create document store - handles column naming automatically")
    print("document_store = DocumentStore(")
    print("    docs=sources,")
    print("    parser=parser,")
    print("    splitter=splitter,")
    print("    retriever_factory=BruteForceKnnFactory(embedder=embedder)")
    print(")")
    print("```")
    print()


if __name__ == "__main__":
    # Show migration guidance when script is run directly
    show_migration_guidance()
    print()
    example_modern_setup()
