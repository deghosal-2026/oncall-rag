from __future__ import annotations

from unittest.mock import patch

from oncall_rag.eval import run_eval
from oncall_rag.retriever import RetrievedChunk


class TestEval:
    def test_returns_metrics_from_eval_file(self, config, eval_json):
        with patch("oncall_rag.eval.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedChunk(text="a", source_file="kubernetes/runbook1.md", start_line=42, end_line=47, score=0.9),
            ]
            results = run_eval(config, eval_path=eval_json)

        assert "mrr" in results
        assert "recall_at_5" in results
        assert results["mrr"] > 0
        assert results["recall_at_5"] > 0

    def test_zero_metrics_when_no_match(self, config, eval_json):
        with patch("oncall_rag.eval.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedChunk(text="a", source_file="other.md", start_line=1, end_line=2, score=0.9),
            ]
            results = run_eval(config, eval_path=eval_json)

        assert results["mrr"] == 0.0
        assert results["recall_at_5"] == 0.0

    def test_handles_missing_eval_file(self, config, tmp_path):
        results = run_eval(config, eval_path=str(tmp_path / "nonexistent.json"))
        assert results["mrr"] == 0.0
        assert "error" in results

    def test_handles_empty_questions(self, config, tmp_path):
        fp = tmp_path / "empty.json"
        fp.write_text('{"questions": []}')
        results = run_eval(config, eval_path=str(fp))
        assert results["mrr"] == 0.0
        assert "error" in results

    def test_mrr_perfect_rank(self, config, eval_json):
        with patch("oncall_rag.eval.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievedChunk(text="a", source_file="kubernetes/runbook1.md", start_line=42, end_line=47, score=0.95),
            ]
            results = run_eval(config, eval_path=eval_json)

        assert results["mrr"] == 0.5  # 1/2 questions match at rank 1
        assert results["recall_at_5"] == 0.5
