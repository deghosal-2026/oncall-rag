from __future__ import annotations

import json
from pathlib import Path

from oncall_rag.config import Config
from oncall_rag.retriever import retrieve


def run_eval(config: Config, eval_path: str = "data/eval.json") -> dict:
    path = Path(eval_path)
    if not path.exists():
        return {"mrr": 0.0, "recall_at_5": 0.0, "error": f"Eval file not found: {eval_path}"}

    data = json.loads(path.read_text())
    questions = data.get("questions", [])

    if not questions:
        return {"mrr": 0.0, "recall_at_5": 0.0, "error": "No questions in eval set"}

    reciprocal_ranks = []
    recall_at_5 = 0

    for q in questions:
        chunks = retrieve(q["question"], config)
        rank = 0
        found = False
        for i, c in enumerate(chunks):
            if c.source_file == q.get("source_file", ""):
                rank = i + 1
                found = True
                break
        if found:
            reciprocal_ranks.append(1.0 / rank)
            if rank <= 5:
                recall_at_5 += 1
        else:
            reciprocal_ranks.append(0.0)

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    recall = recall_at_5 / len(questions) if questions else 0.0

    return {"mrr": round(mrr, 4), "recall_at_5": round(recall, 4)}
