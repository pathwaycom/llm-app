# Migration Guide: Fixing "Table has no column with name doc" Error

This guide addresses the issue reported in [GitHub Issue #52](https://github.com/pathwaycom/llm-app/issues/52) where users encountered the error: `AttributeError: Table has no column with name doc`.

## Problem Description

In earlier versions of the LLM App, the indexing process expected input data to have a specific column named `doc`. When users provided data without this column, the application would fail with the error message "Table has no column with name doc".

## Solution

The current version of the LLM App uses modern abstractions that automatically handle data formatting and column naming. The recommended approach is to use:

1. **DocumentStore** for document management
2. **VectorStoreServer** for vector operations
3. **Proper data connectors** that handle column naming automatically

## Updated Usage Examples

### Using DocumentStore (Recommended)

```python
import pathway as pw
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm import embedders, parsers, splitters
from pathway.stdlib.indexing import BruteForceKnnFactory

# Read documents using Pathway connectors
sources = [
    pw.io.fs.read(
        path="./data",
        format="binary",
        with_metadata=True,
    )
]

# Configure processing components
parser = parsers.UnstructuredParser()
splitter = splitters.TokenCountSplitter(max_tokens=400)
embedder = embedders.OpenAIEmbedder()

# Create retriever factory
retriever_factory = BruteForceKnnFactory(
    reserved_space=1000,
    embedder=embedder,
    metric=pw.stdlib.indexing.BruteForceKnnMetricKind.COS
)

# Create document store - handles column naming automatically
document_store = DocumentStore(
    docs=sources,
    parser=parser,
    splitter=splitter,
    retriever_factory=retriever_factory
)
```

### Using VectorStoreServer (Alternative)

```python
import pathway as pw
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm import embedders, parsers, splitters

# Read documents
folder = pw.io.fs.read(
    path="./data/*.txt",
    format="binary",
    with_metadata=True,
)

# Configure components
parser = parsers.UnstructuredParser()
splitter = splitters.TokenCountSplitter(min_tokens=150, max_tokens=450)
embedder = embedders.OpenAIEmbedder()

# Create vector store server - automatically handles data structure
vector_server = VectorStoreServer(
    folder,
    embedder=embedder,
    splitter=splitter,
    parser=parser,
)

# Run server
vector_server.run_server("0.0.0.0", 8000)
```

## Key Changes from Legacy Code

### Legacy Code (Problematic)

```python
# This would fail if 'doc' column doesn't exist
embedded_data = contextful(context=documents, data_to_embed=documents.doc)
```

### Modern Code (Fixed)

```python
# Modern approach handles column naming automatically
document_store = DocumentStore(docs=sources, parser=parser, splitter=splitter, retriever_factory=retriever_factory)
```

## Data Input Guidelines

When providing data to the modern LLM App:

1. **Use Pathway connectors** (pw.io.fs.read, pw.io.gdrive.read, etc.) which automatically handle data formatting
2. **Set format="binary"** for document files
3. **Include with_metadata=True** for better document tracking
4. **Let the parsers handle column creation** - don't manually create 'doc' columns

## Configuration Examples

### Reading from Files

```yaml
$sources:
  - !pw.io.fs.read
    path: files-for-indexing
    format: binary
    with_metadata: true
```

### Reading from Google Drive

```yaml
$sources:
  - !pw.io.gdrive.read
    object_id: $DRIVE_ID
    service_user_credentials_file: gdrive_indexer.json
    with_metadata: true
```

### Reading from SharePoint

```yaml
$sources:
  - !pw.xpacks.connectors.sharepoint.read
    url: $SHAREPOINT_URL
    tenant: $SHAREPOINT_TENANT
    client_id: $SHAREPOINT_CLIENT_ID
    with_metadata: true
```

## Error Prevention

If you encounter the "Table has no column with name doc" error:

1. **Update to the latest version** of the LLM App
2. **Use DocumentStore or VectorStoreServer** instead of low-level APIs
3. **Use proper data connectors** with format="binary"
4. **Check your data pipeline** - ensure you're not manually creating tables with missing columns

## Additional Resources

- [DocumentStore Documentation](https://pathway.com/developers/api-docs/pathway-xpacks-llm/document_store)
- [VectorStore Documentation](https://pathway.com/developers/api-docs/pathway-xpacks-llm/vectorstore)
- [Data Connectors Guide](https://pathway.com/developers/user-guide/connect/pathway-connectors)
- [LLM XPack Overview](https://pathway.com/developers/user-guide/llm-xpack/overview)
