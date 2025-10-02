# Cast RAG (Retrieval-Augmented Generation)

A complete RAG implementation for Cast knowledge bases that provides semantic search and AI-powered answers using Gemini embeddings and ChromaDB for persistence.

## Features

- **Gemini Embeddings**: Uses Google's `text-embedding-004` model via LiteLLM
- **Incremental Indexing**: Only re-embeds when file content changes (digest-based)
- **Intelligent Chunking**: Whole document → heading-based → paragraph fallback
- **Rename Detection**: Updates metadata without re-embedding when files move
- **Type Filtering**: Ignores files with `type: prompt` or `type: spec`
- **ChromaDB Persistence**: Vector storage under `<root>/.cast/chroma`
- **Offline Testing**: Deterministic fake embeddings for development

## Quick Start

### 1. Setup Environment

```bash
# Set your Cast folder location
export CAST_FOLDER="/path/to/your/Cast"

# Set Gemini API key for real embeddings
export GEMINI_API_KEY="your-gemini-api-key"
# OR
export GOOGLE_API_KEY="your-google-api-key"
```

### 2. Index Your Cast

```python
from casting.cast.query.rag import index_cast

# Build or update the vector index
report = index_cast()
print(f"Added: {report['added']}, Updated: {report['updated']}, Skipped: {report['skipped']}")
```

### 3. Search Your Knowledge Base

```python
from casting.cast.query.rag import search

# Semantic search
hits = search("How do I deploy services?", top_k=5)
for hit in hits:
    print(f"Score: {hit.score:.3f}")
    print(f"File: {hit.metadata['relpath']}")
    print(f"Content: {hit.text[:200]}...")
    print("---")
```

### 4. Get AI-Powered Answers

```python
from casting.cast.query.rag import answer

# Full RAG with LLM
response = answer(
    "How do I rotate API keys?",
    top_k=6,
    model="gemini-1.5-flash"  # or "gpt-4", etc.
)

print("Answer:", response["answer"])
print("Sources:", [h["metadata"]["relpath"] for h in response["hits"]])
```

## CLI Usage

Quick command-line interface for testing:

```bash
# Index with real Gemini embeddings
python -m casting.cast.query.rag index

# Index with fake embeddings (offline)
python -m casting.cast.query.rag index --fake

# Search the index
python -m casting.cast.query.rag search "kubernetes deployment"
python -m casting.cast.query.rag search "API authentication" -k 10
```

## Programmatic API

### Indexing

```python
from casting.cast.query.rag import build_or_update_index, GeminiEmbeddingProvider, FakeDeterministicEmbedding
from pathlib import Path

# Custom indexing with specific embedder
report = build_or_update_index(
    embedder=GeminiEmbeddingProvider(model="text-embedding-004"),
    cleanup_orphans=True,  # Remove records for deleted files
    db_path=Path("/custom/chroma/path")  # Optional custom DB location
)

# Offline indexing for development
report = build_or_update_index(
    embedder=FakeDeterministicEmbedding(dim=64),
    cleanup_orphans=True
)
```

### Search Options

```python
from casting.cast.query.rag import search
from pathlib import Path

# Basic search
hits = search("query text")

# Advanced search
hits = search(
    "deployment strategies",
    top_k=10,
    db_path=Path("/custom/chroma/path")  # Custom DB location
)

# Access hit details
for hit in hits:
    print(f"ID: {hit.id}")
    print(f"Score: {hit.score}")
    print(f"Text: {hit.text}")
    print(f"File: {hit.metadata['relpath']}")
    print(f"Cast ID: {hit.metadata['file_cast_id']}")
    print(f"Title: {hit.metadata['title']}")
```

### Full RAG Answers

```python
from casting.cast.query.rag import answer

# Just retrieval (no LLM)
response = answer("How do I scale services?")
print("Retrieved chunks:", len(response["hits"]))

# With LLM summarization
response = answer(
    "How do I scale services?",
    top_k=8,
    model="gemini-1.5-flash"  # or "gpt-4", "claude-3-sonnet", etc.
)

print("Question:", response["question"])
print("Answer:", response["answer"])
print("Source files:", [h["metadata"]["relpath"] for h in response["hits"]])
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CAST_FOLDER` | Yes | Path to your Cast folder (the one containing markdown files) |
| `GEMINI_API_KEY` | For production | Google Gemini API key for embeddings |
| `GOOGLE_API_KEY` | Alternative | Alternative to `GEMINI_API_KEY` |

### Cast File Structure

Your Cast should have this structure:
```
/path/to/your/project/
├── .cast/
│   └── config.yaml          # Contains cast-id, cast-name, etc.
└── Cast/                    # Your CAST_FOLDER points here
    ├── Notes/
    │   ├── Deployment.md
    │   └── Authentication.md
    ├── Guides/
    │   └── Setup.md
    └── ...
```

### Cast Configuration (`.cast/config.yaml`)

```yaml
cast-id: "your-unique-cast-id"
cast-name: "YourCastName"
cast-location: "Cast"
```

## How It Works

### 1. File Discovery
- Scans `$CAST_FOLDER/**/*.md` for markdown files
- Parses YAML frontmatter looking for `cast-id` field
- Skips files with `type: prompt` or `type: spec`

### 2. Content Processing
- Computes digest of YAML frontmatter + markdown body
- Prepends title as heading: `# {title}\n\n{body}`
- Attempts whole-document embedding first
- Falls back to heading-based chunking if too large
- Finally uses paragraph-based chunking for very long sections

### 3. Incremental Updates
- **Same digest**: Skip (no re-embedding needed)
- **Same digest, different path**: Update metadata only (file renamed)
- **Different digest**: Delete old chunks, re-embed new content
- **Cleanup**: Remove chunks for files no longer on disk

### 4. Vector Storage
- Uses ChromaDB with persistent storage
- Collection name: `cast_{safe_cast_name}` (invalid chars replaced with `_`)
- Chunk IDs: `{file_cast_id}::{chunk_index:04d}`
- Metadata includes: `file_cast_id`, `relpath`, `digest`, `chunk_index`, `title`, `cast_name`

### 5. Search & Retrieval
- Embeds query using same provider as indexing
- Performs cosine similarity search in ChromaDB
- Returns results with similarity scores (0-1, higher = more similar)

## Advanced Usage

### Custom Embedding Providers

```python
from casting.cast.query.rag.embeddings import EmbeddingProvider

class MyCustomEmbedder(EmbeddingProvider):
    max_chars = 8000  # Provider's context limit

    def embed_texts(self, texts):
        # Your custom embedding logic
        return [[0.1, 0.2, ...] for _ in texts]

# Use in indexing
from casting.cast.query.rag import build_or_update_index
report = build_or_update_index(embedder=MyCustomEmbedder())
```

### Batch Processing

```python
# Index multiple casts
casts = ["/path/to/cast1/Cast", "/path/to/cast2/Cast"]

for cast_path in casts:
    os.environ["CAST_FOLDER"] = cast_path
    report = index_cast()
    print(f"Indexed {cast_path}: {report}")
```

### Production Monitoring

```python
# Monitor indexing results
report = index_cast()

if report["added"] > 0:
    print(f"Added {report['added']} new files")
if report["updated"] > 0:
    print(f"Updated {report['updated']} changed files")
if report["deleted_orphans"] > 0:
    print(f"Cleaned up {report['deleted_orphans']} orphaned records")

print(f"Total chunks in index: {report['chunks']}")
```

## Troubleshooting

### Common Issues

1. **`CAST_FOLDER env var is not set`**
   - Set `export CAST_FOLDER="/path/to/your/Cast"`
   - Make sure it points to the folder containing your `.md` files

2. **`.cast directory not found`**
   - Ensure `.cast/config.yaml` exists in the parent directory of your Cast folder
   - Check that `config.yaml` has required fields: `cast-id`, `cast-name`

3. **`LiteLLM not available`**
   - Install dependencies: `uv sync` or `pip install litellm chromadb`

4. **Embedding dimension mismatch**
   - Delete the ChromaDB directory: `rm -rf .cast/chroma`
   - Re-run indexing to recreate with correct dimensions

5. **No search results**
   - Verify files were indexed: check `report["added"]` and `report["chunks"]`
   - Try broader search terms
   - Check that files have `cast-id` in frontmatter

### Debug Mode

```python
# Enable verbose output
import logging
logging.basicConfig(level=logging.DEBUG)

# Check what files are being indexed
from casting.cast.query.rag.indexer import _iter_files_to_index
from pathlib import Path

vault_path = Path(os.environ["CAST_FOLDER"])
files = list(_iter_files_to_index(vault_path))
print(f"Found {len(files)} indexable files:")
for f in files[:5]:  # Show first 5
    print(f"  {f.relpath} (cast-id: {f.cast_id})")
```

### Performance Tips

1. **Large Collections**: Use smaller `top_k` values for faster search
2. **Incremental Updates**: Run indexing regularly; unchanged files are skipped
3. **Memory Usage**: For very large casts, consider chunking with smaller `max_chars`
4. **Network Costs**: Use fake embeddings for development, real embeddings for production

## Integration Examples

### CI/CD Pipeline

```bash
#!/bin/bash
# .github/workflows/update-index.yml

export CAST_FOLDER="$GITHUB_WORKSPACE/knowledge/Cast"
export GEMINI_API_KEY="$GEMINI_API_KEY"

# Update search index on main branch
python -m casting.cast.query.rag index

# Upload ChromaDB to S3/cloud storage if needed
aws s3 sync .cast/chroma s3://your-bucket/chroma/
```

### Web API

```python
from fastapi import FastAPI
from casting.cast.query.rag import search, answer

app = FastAPI()

@app.get("/search")
def search_knowledge(q: str, limit: int = 5):
    hits = search(q, top_k=limit)
    return {"query": q, "results": [h.__dict__ for h in hits]}

@app.get("/ask")
def ask_question(q: str, model: str = "gemini-1.5-flash"):
    response = answer(q, model=model)
    return response
```

### Slack Bot

```python
import os
from slack_sdk import WebClient
from casting.cast.query.rag import answer

slack = WebClient(token=os.environ["SLACK_TOKEN"])

@app.event("message")
def handle_question(event):
    if event.get("text", "").startswith("!ask "):
        question = event["text"][5:]  # Remove "!ask "
        response = answer(question, model="gemini-1.5-flash")

        slack.chat_postMessage(
            channel=event["channel"],
            text=f"**Answer:** {response['answer']}\n\n**Sources:** {', '.join(h['metadata']['relpath'] for h in response['hits'][:3])}"
        )
```

## License

This RAG implementation is part of the Cast project and follows the same licensing terms.