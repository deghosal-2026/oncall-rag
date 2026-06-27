from __future__ import annotations

import pytest

from oncall_rag.indexer import _walk_markdown, _split_file


class TestWalkMarkdown:
    def test_returns_md_files(self, small_corpus):
        files = _walk_markdown(small_corpus)
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)

    def test_skips_non_md(self, tmp_path):
        (tmp_path / "notes.txt").write_text("hello")
        (tmp_path / "readme.md").write_text("# Hello")
        files = _walk_markdown(str(tmp_path))
        assert len(files) == 1
        assert files[0].name == "readme.md"

    def test_skips_huge_files(self, large_file_corpus):
        files = _walk_markdown(large_file_corpus)
        assert len(files) == 0

    def test_raises_on_missing_path(self):
        with pytest.raises(FileNotFoundError):
            _walk_markdown("/nonexistent/path")

    def test_recursive_discovery(self, tmp_path):
        a = tmp_path / "a"
        b = a / "b"
        b.mkdir(parents=True)
        (a / "root.md").write_text("root")
        (b / "nested.md").write_text("nested")
        files = _walk_markdown(str(tmp_path))
        assert len(files) == 2


class TestSplitFile:
    def test_splits_into_chunks(self, tmp_path):
        fp = tmp_path / "doc.md"
        fp.write_text("# Title\n\nParagraph one.\n\nParagraph two.\n\nParagraph three.\n")
        chunks = _split_file(fp, chunk_size=50, chunk_overlap=10)
        assert len(chunks) > 1
        assert all(c.text.strip() for c in chunks)

    def test_single_chunk_for_small_file(self, tmp_path):
        fp = tmp_path / "small.md"
        fp.write_text("# Just one header\n")
        chunks = _split_file(fp, chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 1
        assert chunks[0].text.strip() == "# Just one header"

    def test_tracks_line_numbers(self, tmp_path):
        fp = tmp_path / "lines.md"
        fp.write_text("line1\nline2\nline3\nline4\nline5\n")
        chunks = _split_file(fp, chunk_size=10, chunk_overlap=2)
        for c in chunks:
            assert c.start_line >= 1
            assert c.end_line >= c.start_line
            assert c.source_file == str(fp)

    def test_skips_empty_chunks(self, tmp_path):
        fp = tmp_path / "empty.md"
        fp.write_text("valid\n\n\n\n\nmore\n")
        chunks = _split_file(fp, chunk_size=10, chunk_overlap=2)
        assert all(c.text.strip() for c in chunks)
