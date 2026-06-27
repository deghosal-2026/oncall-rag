from __future__ import annotations

import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "oncall_rag", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "index" in result.stdout
    assert "query" in result.stdout
    assert "eval" in result.stdout


def test_cli_index_no_path_shows_error():
    result = subprocess.run(
        [sys.executable, "-m", "oncall_rag", "index"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0  # missing required argument
