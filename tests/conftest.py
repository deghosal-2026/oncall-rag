from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oncall_rag.config import Config


@pytest.fixture(autouse=True)
def _clear_caches():
    from oncall_rag import indexer, retriever
    indexer._embeddings_cache.clear()
    retriever._embeddings_cache.clear()
    retriever._vectorstore_cache.clear()
    yield


@pytest.fixture
def config():
    return Config(
        chroma_path="/tmp/test_chroma_db",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=500,
        chunk_overlap=50,
        top_k=5,
    )


@pytest.fixture
def small_corpus(tmp_path: Path):
    """Create a temporary corpus with a few markdown files."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "runbook1.md").write_text(
        "# Runbook 1\n\nStep 1: Check logs.\nStep 2: Restart service.\n"
    )
    (docs / "runbook2.md").write_text(
        "# Runbook 2\n\n## Debugging\n\nRun `kubectl get pods`.\n"
    )
    return str(docs)


@pytest.fixture
def large_file_corpus(tmp_path: Path):
    """Corpus with a file exceeding 1MB to test skip logic."""
    docs = tmp_path / "docs"
    docs.mkdir()
    fp = docs / "huge.md"
    with open(fp, "w") as f:
        f.write("x" * 1_500_000)
    return str(docs)


@pytest.fixture
def eval_json(tmp_path: Path):
    """Create a temporary eval.json file."""
    data = {
        "questions": [
            {
                "id": "k8s-001",
                "question": "How do I check why a pod is in CrashLoopBackOff?",
                "answer": "Run kubectl describe pod.",
                "source_file": "kubernetes/runbook1.md",
                "source_lines": "42-47",
            },
            {
                "id": "k8s-002",
                "question": "How to restart a pod?",
                "answer": "Run kubectl delete pod.",
                "source_file": "kubernetes/runbook2.md",
                "source_lines": "10-15",
            },
        ]
    }
    fp = tmp_path / "eval.json"
    fp.write_text(json.dumps(data))
    return str(fp)


@pytest.fixture
def mock_vectorstore():
    """Mock a Chroma vector store for retrieval tests."""
    with patch("oncall_rag.retriever.Chroma") as mock:
        instance = mock.return_value
        instance.similarity_search_with_score.return_value = [
            (MagicMock(page_content="Step 1: Check logs.", metadata={"source_file": "runbook1.md", "start_line": 3, "end_line": 4}), 0.85),
            (MagicMock(page_content="Step 2: Restart service.", metadata={"source_file": "runbook1.md", "start_line": 5, "end_line": 6}), 0.72),
        ]
        yield instance


@pytest.fixture
def mock_embeddings():
    with patch("oncall_rag.indexer.HuggingFaceEmbeddings") as mock:
        yield mock
