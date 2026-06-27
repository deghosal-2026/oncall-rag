from __future__ import annotations

from unittest.mock import patch

from oncall_rag.indexer import index_documents
from oncall_rag.responder import query_runbooks


class TestIndexQueryFlow:
    def test_index_returns_summary(self, config, small_corpus):
        with patch("oncall_rag.indexer.Chroma") as mock_chroma, \
             patch("oncall_rag.indexer.HuggingFaceEmbeddings"):
            instance = mock_chroma.return_value
            result = index_documents(small_corpus, config)
        assert result["files_indexed"] == 2
        assert result["chunks_created"] >= 2
        instance.add_texts.assert_called()

    def test_index_empty_corpus_returns_zero(self, config, tmp_path):
        with patch("oncall_rag.indexer.HuggingFaceEmbeddings"):
            result = index_documents(str(tmp_path), config)
        assert result == {"files_indexed": 0, "chunks_created": 0}

    def test_index_with_rebuild(self, config, small_corpus):
        with patch("oncall_rag.indexer.Chroma") as mock_chroma, \
             patch("oncall_rag.indexer.HuggingFaceEmbeddings"), \
             patch("shutil.rmtree") as mock_rmtree:
            instance = mock_chroma.return_value
            result = index_documents(small_corpus, config, rebuild=True)
        assert result["files_indexed"] == 2
        mock_rmtree.assert_called_once()

    def test_query_returns_answer_with_sources(self, config):
        with patch("oncall_rag.responder.retrieve") as mock_retrieve, \
             patch("oncall_rag.llm.omlx.OmlxClient") as mock_client:
            mock_retrieve.return_value = [
                _chunk("Check logs.", "runbook1.md", 3, 4, 0.9),
                _chunk("Restart service.", "runbook1.md", 5, 6, 0.8),
            ]
            client_instance = mock_client.return_value
            client_instance.generate.return_value = "Check logs then restart service."

            result = query_runbooks("How to fix?", config)

        assert "Check logs then restart service." in result
        assert "Sources:" in result
        assert "runbook1.md:3-4" in result

    def test_query_returns_no_runbook_when_empty_retrieval(self, config):
        with patch("oncall_rag.responder.retrieve") as mock_retrieve:
            mock_retrieve.return_value = []
            result = query_runbooks("unknown", config)
        assert result == "I don't have a runbook for this."

    def test_query_falls_back_to_sources_on_llm_error(self, config):
        with patch("oncall_rag.responder.retrieve") as mock_retrieve, \
             patch("oncall_rag.llm.omlx.OmlxClient") as mock_client:
            mock_retrieve.return_value = [
                _chunk("Check logs.", "runbook1.md", 3, 4, 0.9),
            ]
            client_instance = mock_client.return_value
            client_instance.generate.side_effect = Exception("LLM down")

            result = query_runbooks("How to fix?", config)

        assert "Sources:" in result
        assert "runbook1.md:3-4" in result


def _chunk(text, source, start, end, score):
    from oncall_rag.retriever import RetrievedChunk
    return RetrievedChunk(text=text, source_file=source, start_line=start, end_line=end, score=score)
