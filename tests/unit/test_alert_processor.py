from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from oncall_rag.alert_schema import Alert, AlertResult
from oncall_rag.alert_processor import process_alerts, _build_question
from oncall_rag.config import Config


class TestAlertSchema:
    def test_alert_defaults(self):
        alert = Alert(alert_id="test-001", title="Test Alert", message="Something happened")
        assert alert.alert_id == "test-001"
        assert alert.service == "unknown"
        assert alert.severity == "warning"
        assert alert.labels == {}
        assert alert.timestamp != ""

    def test_alert_from_dict(self):
        raw = {
            "alert_id": "k8s-001",
            "title": "Pod CrashLoopBackOff",
            "message": "Pod is down",
            "service": "kubernetes",
            "severity": "critical",
            "labels": {"namespace": "default"},
        }
        alert = Alert(**raw)
        assert alert.service == "kubernetes"
        assert alert.severity == "critical"
        assert alert.labels["namespace"] == "default"

    def test_alert_result_defaults(self):
        r = AlertResult(alert_id="test-001", title="Test Alert")
        assert r.processed_at != ""
        assert r.answer == ""
        assert r.sources == []
        assert r.has_runbook is False


class TestBuildQuestion:
    def test_builds_from_title_and_message(self):
        alert = Alert(alert_id="x", title="Pod CrashLoopBackOff", message="Pod nginx is down")
        q = _build_question(alert)
        assert "Pod CrashLoopBackOff" in q
        assert "Pod nginx is down" in q

    def test_builds_from_title_only(self):
        alert = Alert(alert_id="x", title="Pod CrashLoopBackOff", message="")
        q = _build_question(alert)
        assert q == "Pod CrashLoopBackOff"


class TestProcessAlerts:
    def test_empty_inbox(self, config: Config):
        result = process_alerts(config)
        assert result == {"processed": 0, "errors": 0}

    def test_processes_alerts_and_moves_files(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("oncall_rag.alert_processor.INBOX_DIR", tmp_path / "inbox")
        monkeypatch.setattr("oncall_rag.alert_processor.OUTBOX_DIR", tmp_path / "outbox")
        monkeypatch.setattr("oncall_rag.alert_processor.ARCHIVE_DIR", tmp_path / "archive")

        inbox = tmp_path / "inbox"
        inbox.mkdir()
        alert = {
            "alert_id": "test-001",
            "title": "Test Alert",
            "message": "Something went wrong",
            "service": "test",
            "severity": "critical",
        }
        (inbox / "test-001.json").write_text(json.dumps(alert))

        config = Config()

        with patch("oncall_rag.responder.query_runbooks") as mock_query:
            mock_query.return_value = "Step 1: Check logs.\n\nSources:\n  - test.md:1-5"
            result = process_alerts(config)

        assert result["processed"] == 1
        assert result["errors"] == 0

        outbox = tmp_path / "outbox"
        archive = tmp_path / "archive"
        assert (outbox / "test-001.json").exists()
        assert (archive / "test-001.json").exists()
        assert not (inbox / "test-001.json").exists()

        out_data = json.loads((outbox / "test-001.json").read_text())
        assert out_data["alert_id"] == "test-001"
        assert out_data["has_runbook"] is True
        assert out_data["sources"] == ["test.md:1-5"]

    def test_handles_invalid_alert_gracefully(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("oncall_rag.alert_processor.INBOX_DIR", tmp_path / "inbox")
        monkeypatch.setattr("oncall_rag.alert_processor.OUTBOX_DIR", tmp_path / "outbox")
        monkeypatch.setattr("oncall_rag.alert_processor.ARCHIVE_DIR", tmp_path / "archive")

        inbox = tmp_path / "inbox"
        inbox.mkdir()
        (inbox / "bad.json").write_text("not valid json")

        result = process_alerts(Config())
        assert result["errors"] == 1
        assert result["processed"] == 0
