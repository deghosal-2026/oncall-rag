from __future__ import annotations

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


def _split_file(file: Path, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    text = file.read_text(encoding="utf-8", errors="replace")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    lines = text.split("\n")
    chunks = []
    for seg in splitter.split_text(text):
        if not seg.strip():
            continue
        start = text[: text.index(seg)].count("\n") + 1 if seg in text else 1
        end = start + seg.count("\n")
        chunks.append(Chunk(text=seg, source_file=str(file), start_line=start, end_line=end))
    return chunks


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
        chunks = _split_file(file, config.chunk_size, config.chunk_overlap)
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
