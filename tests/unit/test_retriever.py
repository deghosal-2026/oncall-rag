from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oncall_rag.retriever import retrieve, RetrievedChunk


class TestRetrieve:
    def test_returns_retrieved_chunks(self, config, mock_vectorstore):
        chunks = retrieve("How to check logs?", config)
        assert len(chunks) == 2
        assert all(isinstance(c, RetrievedChunk) for c in chunks)
        assert chunks[0].text == "Step 1: Check logs."
        assert chunks[0].source_file == "runbook1.md"
        assert chunks[0].score == 0.85

    def test_returns_empty_on_no_results(self, config):
        with patch("oncall_rag.retriever.Chroma") as mock_cls:
            instance = mock_cls.return_value
            instance.similarity_search_with_score.return_value = []
            chunks = retrieve("something random", config)
        assert chunks == []

    def test_handles_missing_metadata(self, config):
        with patch("oncall_rag.retriever.Chroma") as mock_cls:
            instance = mock_cls.return_value
            instance.similarity_search_with_score.return_value = [
                (MagicMock(page_content="text", metadata={}), 0.5)
            ]
            chunks = retrieve("test", config)
        assert len(chunks) == 1
        assert chunks[0].source_file == "unknown"
        assert chunks[0].start_line == 0
        assert chunks[0].end_line == 0

    def test_passes_query_and_top_k(self, config, mock_vectorstore):
        retrieve("test query", config)
        mock_vectorstore.similarity_search_with_score.assert_called_once_with(
            "test query", k=5
        )
