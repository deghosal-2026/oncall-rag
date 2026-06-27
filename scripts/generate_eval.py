from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from oncall_rag.config import load_config
from oncall_rag.llm.omlx import OmlxClient

SYSTEM_PROMPT = (
    "You are an eval-set generator for a runbook RAG assistant. "
    "Given a runbook file, generate question-answer pairs that test retrieval accuracy. "
    "Each pair must reference an existing section of the file with correct source line ranges. "
    "Output valid JSON only — no markdown, no preamble."
)

USER_TEMPLATE = """Read this runbook file and generate {pairs_per_file} question-answer pairs that would test an on-call engineer's ability to find the right procedure.

File: {filename}

Content:
{content}

For each pair, the question should be a realistic on-call query ("How do I...", "What should I do when...", "Why is my..."). The answer should quote or summarize the relevant section. The source_lines should be the exact start-end line range from the file above.

Respond with a JSON array only:
[
  {{
    "id": "{prefix}-N",
    "question": "...",
    "answer": "...",
    "source_file": "{filename}",
    "source_lines": "start-end"
  }}
]"""


def extract_json(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def file_identifier(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return f"corpus/{rel}"


def main():
    config = load_config()
    corpus_root = Path("corpus")
    pairs_per_file = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    client = OmlxClient(
        endpoint=config.omlx_endpoint,
        model=config.omlx_model,
        system_prompt=SYSTEM_PROMPT,
    )

    all_questions: list[dict] = []
    files = sorted(corpus_root.rglob("*.md"))
    n = 1

    for fp in files:
        rel = file_identifier(fp, corpus_root)
        content = fp.read_text(encoding="utf-8", errors="replace")
        lines = content.count("\n") + 1
        if lines < 3 or len(content) < 50:
            continue

        print(f"  {rel} ({lines} lines)...", end=" ", flush=True)
        prompt = USER_TEMPLATE.format(
            pairs_per_file=pairs_per_file,
            filename=rel,
            content=content,
            prefix=f"gen-{n:04d}",
        )

        try:
            raw = client.generate(prompt, temperature=0.3)
            pairs = extract_json(raw)
            for p in pairs:
                p["id"] = f"eval-{n:04d}"
                n += 1
            all_questions.extend(pairs)
            print(f"{len(pairs)} pairs")
        except Exception as e:
            print(f"SKIP: {e}")

    out = Path("data/eval.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"questions": all_questions}, indent=2))
    print(f"\nSaved {len(all_questions)} questions to {out}")


if __name__ == "__main__":
    main()
