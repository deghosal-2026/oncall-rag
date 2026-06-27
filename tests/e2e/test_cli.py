from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "oncall_rag", *args],
        capture_output=True,
        text=True,
        env=env,
    )


class TestHelp:
    def test_cli_help(self):
        result = _run("--help")
        assert result.returncode == 0
        assert "index" in result.stdout
        assert "query" in result.stdout
        assert "eval" in result.stdout
        assert "chunking-experiment" in result.stdout


class TestIndex:
    def test_index_missing_path(self):
        result = _run("index")
        assert result.returncode != 0

    def test_index_nonexistent_path(self):
        result = _run("index", "/nonexistent/path")
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_index_empty_dir(self, tmp_path: Path):
        d = tmp_path / "empty"
        d.mkdir()
        result = _run("index", str(d))
        assert result.returncode == 0
        assert "0 files" in result.stdout

    def test_index_small_corpus(self, tmp_path: Path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        (corpus / "runbook.md").write_text("# Debugging\n\nStep 1: Check logs.\nStep 2: Restart.\n")
        result = _run("index", str(corpus))
        assert result.returncode == 0
        assert "Indexed" in result.stdout

    def test_index_skips_large_file(self, tmp_path: Path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        fp = corpus / "huge.md"
        fp.write_text("x" * 1_500_000)
        (corpus / "small.md").write_text("# Small\n\nContent.\n")
        result = _run("index", str(corpus))
        assert "Indexed" in result.stdout

    def test_index_rebuild(self, tmp_path: Path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        (corpus / "runbook.md").write_text("# Rebuild test\n\nContent.\n")
        _run("index", str(corpus))
        result = _run("index", str(corpus), "--rebuild")
        assert result.returncode == 0
        assert "Indexed" in result.stdout


class TestEval:
    def test_eval_without_index_handles_gracefully(self, tmp_path: Path):
        result = _run("eval")
        assert result.returncode == 0


class TestChunkingExperiment:
    def test_experiment_runs(self, tmp_path: Path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        (corpus / "runbook.md").write_text("# Debugging\n\nStep 1: Check.\n")
        eval_path = tmp_path / "eval.json"
        eval_path.write_text(json.dumps({
            "questions": [
                {
                    "id": "test-001",
                    "question": "How to check?",
                    "answer": "Step 1: Check.",
                    "source_file": str(corpus / "runbook.md"),
                    "source_lines": "1-4",
                }
            ]
        }))
        result = _run("chunking-experiment", str(corpus), "--eval", str(eval_path), "--output", str(tmp_path / "report.md"))
        assert result.returncode == 0
        assert "recursive" in result.stdout
        assert "header-split" in result.stdout
        assert "fixed-size" in result.stdout
