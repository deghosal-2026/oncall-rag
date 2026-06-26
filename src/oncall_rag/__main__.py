from __future__ import annotations

import argparse

from oncall_rag.config import load_config


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(prog="oncall-rag", description="Runbook RAG assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    index_parser = sub.add_parser("index", help="Ingest markdown files into ChromaDB")
    index_parser.add_argument("path", help="Directory of markdown files")
    index_parser.add_argument("--rebuild", action="store_true", help="Drop and recreate collection")

    query_parser = sub.add_parser("query", help="Ask a question from runbooks")
    query_parser.add_argument("question", help="Your question")

    sub.add_parser("eval", help="Run eval set and print metrics")

    args = parser.parse_args()

    if args.command == "index":
        from oncall_rag.indexer import index_documents
        result = index_documents(args.path, config, rebuild=args.rebuild)
        print(f"Indexed {result['files_indexed']} files, {result['chunks_created']} chunks")

    elif args.command == "query":
        from oncall_rag.responder import query_runbooks
        response = query_runbooks(args.question, config)
        print(response)

    elif args.command == "eval":
        from oncall_rag.eval import run_eval
        results = run_eval(config)
        print(f"MRR: {results['mrr']:.3f}, Recall@5: {results['recall_at_5']:.3f}")


if __name__ == "__main__":
    main()
