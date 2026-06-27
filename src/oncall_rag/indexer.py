from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


@dataclass
class Chunk:
    text: str
    source_file: str
    start_line: int
    end_line: int


def _walk_markdown(path: str) -> list[Path]:
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    files = []
    for f in root.rglob("*.md"):
        if f.is_file() and f.stat().st_size <= 1_000_000:
            files.append(f)
    return files


def _text_to_chunks(text: str, file: Path, segments: list[str]) -> list[Chunk]:
    chunks = []
    for seg in segments:
        if not seg.strip():
            continue
        start = text[: text.index(seg)].count("\n") + 1 if seg in text else 1
        end = start + seg.count("\n")
        chunks.append(Chunk(text=seg, source_file=str(file), start_line=start, end_line=end))
    return chunks


def _split_recursive(text: str, file: Path, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    return _text_to_chunks(text, file, splitter.split_text(text))


def _split_fixed_size(text: str, file: Path, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    segments = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            end = text.rfind(" ", start, end + 1)
            if end == -1 or end <= start:
                end = min(start + chunk_size, len(text))
        segments.append(text[start:end])
        start = end - chunk_overlap if end - chunk_overlap > start else end
    return _text_to_chunks(text, file, segments)


def _split_header(text: str, file: Path, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    lines = text.split("\n")
    sections = []
    current = []
    for line in lines:
        if re.match(r"^#{1,6}\s", line) and current:
            sections.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        sections.append("\n".join(current))
    if not sections:
        sections = [text]
    merged = []
    buffer = ""
    for sec in sections:
        if len(buffer) + len(sec) <= chunk_size * 1.5 or not buffer:
            buffer += ("\n" if buffer else "") + sec
        else:
            merged.append(buffer)
            buffer = sec
    if buffer:
        merged.append(buffer)
    return _text_to_chunks(text, file, merged)


def _split_file(file: Path, chunk_size: int, chunk_overlap: int, strategy: str) -> list[Chunk]:
    text = file.read_text(encoding="utf-8", errors="replace")
    if strategy == "fixed-size":
        return _split_fixed_size(text, file, chunk_size, chunk_overlap)
    elif strategy == "header-split":
        return _split_header(text, file, chunk_size, chunk_overlap)
    return _split_recursive(text, file, chunk_size, chunk_overlap)


def _make_embedding_model(model_name: str):
    return HuggingFaceEmbeddings(model_name=model_name)


def index_documents(
    path: str,
    config,
    rebuild: bool = False,
) -> dict:
    files = _walk_markdown(path)
    if not files:
        return {"files_indexed": 0, "chunks_created": 0}

    embeddings = _make_embedding_model(config.embedding_model)

    persist = config.chroma_path
    if rebuild:
        import shutil
        shutil.rmtree(persist, ignore_errors=True)

    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=persist,
        collection_name="runbooks",
    )

    total_chunks = 0
    for file in files:
        chunks = _split_file(file, config.chunk_size, config.chunk_overlap, config.chunking_strategy)
        if not chunks:
            continue
        texts = [c.text for c in chunks]
        metadatas = [
            {"source_file": c.source_file, "start_line": c.start_line, "end_line": c.end_line}
            for c in chunks
        ]
        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        total_chunks += len(chunks)

    vectorstore.persist()
    return {"files_indexed": len(files), "chunks_created": total_chunks}
