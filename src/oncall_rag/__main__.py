from __future__ import annotations

import argparse
import json

from oncall_rag.config import load_config, Config


def run_experiment(config: Config, corpus_path: str, eval_path: str = "data/eval.json") -> dict:
    strategies = ["recursive", "header-split", "fixed-size"]
    results = {}
    for strategy in strategies:
        print(f"\n--- Strategy: {strategy} ---")
        cfg = config.model_copy()
        cfg.chunking_strategy = strategy
        safe = strategy.replace("-", "_")
        cfg.chroma_path = f"data/chroma_db_{safe}"

        from oncall_rag.indexer import index_documents
        index_documents(corpus_path, cfg, rebuild=True)

        from oncall_rag.eval import run_eval
        metrics = run_eval(cfg, eval_path)
        print(f"  MRR: {metrics['mrr']:.4f}, Recall@5: {metrics['recall_at_5']:.4f}")
        results[strategy] = {"mrr": metrics["mrr"], "recall_at_5": metrics["recall_at_5"]}
    return results


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

    exp_parser = sub.add_parser("chunking-experiment", help="Compare chunking strategies on eval set")
    exp_parser.add_argument("path", help="Directory of markdown files")
    exp_parser.add_argument("--eval", default="data/eval.json", help="Eval set path")
    exp_parser.add_argument("--output", default="docs/chunking-experiment.md", help="Output report path")

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

    elif args.command == "chunking-experiment":
        results = run_experiment(config, args.path, args.eval)
        print("\n" + "=" * 50)
        print("CHUNKING EXPERIMENT RESULTS")
        print("=" * 50)
        print(f"{'Strategy':<20} {'MRR':<10} {'Recall@5':<10}")
        print("-" * 40)
        for strategy, metrics in results.items():
            print(f"{strategy:<20} {metrics['mrr']:<10.4f} {metrics['recall_at_5']:<10.4f}")
        with open(args.output, "w") as f:
            f.write(generate_report(results))
        print(f"\nReport written to {args.output}")


def generate_report(results: dict) -> str:
    lines = []
    lines.append("# Chunking Experiment Report\n")
    lines.append("Compare 3 strategies on the eval set.\n")
    lines.append("| Strategy | MRR | Recall@5 |")
    lines.append("|---|---|---|")
    best = max(results, key=lambda s: results[s]["mrr"])
    for strategy, metrics in results.items():
        star = " ★" if strategy == best else ""
        lines.append(f"| {strategy}{star} | {metrics['mrr']:.4f} | {metrics['recall_at_5']:.4f} |")
    lines.append(f"\n**Recommendation:** `{best}` had the highest MRR.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
