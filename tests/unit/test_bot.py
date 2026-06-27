from __future__ import annotations

import json
from pathlib import Path

import pytest
from discord import Embed

from oncall_rag.bot import (
    _answer_to_embed,
    _log_feedback,
    _log_query,
    _parse_sources,
)


class TestParseSources:
    def test_parses_sources_from_full_answer(self):
        raw = "Step 1: Check logs.\n\nSources:\n  - runbook1.md:3-4\n  - runbook2.md:10-15"
        sources = _parse_sources(raw)
        assert sources == ["runbook1.md:3-4", "runbook2.md:10-15"]

    def test_parses_sources_only(self):
        raw = "Sources:\n  - runbook1.md:3-4"
        sources = _parse_sources(raw)
        assert sources == ["runbook1.md:3-4"]

    def test_returns_empty_for_no_runbook(self):
        assert _parse_sources("I don't have a runbook for this.") == []

    def test_returns_empty_when_no_sources(self):
        assert _parse_sources("Plain answer without sources.") == []


class TestAnswerToEmbed:
    def test_no_runbook_embed(self):
        embed, sources = _answer_to_embed("I don't have a runbook for this.")
        assert isinstance(embed, Embed)
        assert embed.title == "No runbook found"
        assert embed.description == "I don't have a runbook for this."
        assert sources == []

    def test_full_answer_embed(self):
        raw = "Step 1: Check logs.\n\nSources:\n  - runbook1.md:3-4"
        embed, sources = _answer_to_embed(raw)
        assert isinstance(embed, Embed)
        assert embed.title == "Answer"
        assert embed.description and "Step 1: Check logs." in embed.description
        assert embed.fields and embed.fields[0].value == "`runbook1.md:3-4`"
        assert sources == ["runbook1.md:3-4"]

    def test_sources_only_embed(self):
        raw = "Sources:\n  - runbook1.md:3-4"
        embed, sources = _answer_to_embed(raw)
        assert embed.title == "Answer"
        assert embed.description and "No LLM answer" in embed.description
        assert sources == ["runbook1.md:3-4"]

    def test_plain_answer_embed(self):
        raw = "Just a plain answer without sources"
        embed, sources = _answer_to_embed(raw)
        assert embed.title == "Answer"
        assert embed.description == raw
        assert sources == []
        assert not embed.fields


class TestLogFeedback:
    def test_writes_jsonl_entry(self, tmp_path: Path, monkeypatch):
        path = tmp_path / "feedback.jsonl"
        monkeypatch.setattr("oncall_rag.bot.FEEDBACK_PATH", path)
        _log_feedback("test question", "test answer", ["src.md:1-2"], "up", 12345)
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["question"] == "test question"
        assert entry["answer"] == "test answer"
        assert entry["sources"] == ["src.md:1-2"]
        assert entry["rating"] == "up"
        assert entry["user_id"] == 12345
        assert "timestamp" in entry

    def test_appends_multiple_entries(self, tmp_path: Path, monkeypatch):
        path = tmp_path / "feedback.jsonl"
        monkeypatch.setattr("oncall_rag.bot.FEEDBACK_PATH", path)
        _log_feedback("q1", "a1", [], "up", 1)
        _log_feedback("q2", "a2", [], "down", 2)
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2


class TestLogQuery:
    def test_writes_jsonl_entry(self, tmp_path: Path, monkeypatch):
        path = tmp_path / "queries.jsonl"
        monkeypatch.setattr("oncall_rag.bot.QUERIES_PATH", path)
        _log_query("test question", "test answer", ["src.md:1-2"])
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["question"] == "test question"
        assert entry["has_sources"] is True

    def test_has_sources_false(self, tmp_path: Path, monkeypatch):
        path = tmp_path / "queries.jsonl"
        monkeypatch.setattr("oncall_rag.bot.QUERIES_PATH", path)
        _log_query("no source question", "I don't know", [])
        entry = json.loads(path.read_text().strip())
        assert entry["has_sources"] is False
