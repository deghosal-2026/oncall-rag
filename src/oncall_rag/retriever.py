from __future__ import annotations

from dataclasses import dataclass

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


@dataclass
class RetrievedChunk:
    text: str
    source_file: str
    start_line: int
    end_line: int
    score: float


def retrieve(query: str, config) -> list[RetrievedChunk]:
    embeddings = HuggingFaceEmbeddings(model_name=config.embedding_model)
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=config.chroma_path,
        collection_name="runbooks",
    )
    results = vectorstore.similarity_search_with_score(query, k=config.top_k)
    chunks = []
    for doc, score in results:
        meta = doc.metadata
        chunks.append(
            RetrievedChunk(
                text=doc.page_content,
                source_file=meta.get("source_file", "unknown"),
                start_line=int(meta.get("start_line", 0)),
                end_line=int(meta.get("end_line", 0)),
                score=score,
            )
        )
    return chunks
