"""Lantern – Evaluation scoring script.

Compares local vs cloud responses on eval/questions.jsonl questions.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lantern.config import load_settings
from lantern.connectivity import ConnectivityMonitor
from lantern.db import Database
from lantern.models import Msg
from lantern.router import BrainRouter


async def run_eval() -> None:
    settings = load_settings()
    db = Database("eval_test.db")
    conn = ConnectivityMonitor(settings)
    router = BrainRouter(settings, conn, db)

    questions_file = Path(__file__).parent / "questions.jsonl"
    if not questions_file.exists():
        print(f"File not found: {questions_file}")
        return

    items = [json.loads(line) for line in questions_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Evaluating {len(items)} questions with local model '{settings.local_model}'...")

    results = []
    for item in items:
        qid = item["id"]
        q_text = item["question"]
        expected = item["expected"]

        print(f"[{qid}/20] {q_text[:50]}...", end=" ", flush=True)
        messages = [Msg(role="user", content=q_text)]
        try:
            comp = await router.complete(messages, prefer_cloud=False)
            found = expected.lower() in comp.text.lower()
            results.append({
                "id": qid,
                "category": item["category"],
                "question": q_text,
                "expected": expected,
                "answer": comp.text,
                "match": found,
                "latency_ms": comp.latency_ms,
            })
            print(f"✅ ({comp.latency_ms}ms)" if found else f"⚠️ (expected '{expected}')")
        except Exception as exc:
            print(f"❌ Error: {exc}")
            results.append({
                "id": qid,
                "category": item["category"],
                "question": q_text,
                "expected": expected,
                "error": str(exc),
                "match": False,
            })

    total = len(results)
    matched = sum(1 for r in results if r.get("match"))
    print("\n" + "=" * 50)
    print(f"Evaluation Complete: {matched}/{total} ({matched/total*100:.1f}%) matched keyword criteria.")
    print("=" * 50)

    out_file = Path(__file__).parent / "eval_results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Detailed logs saved to {out_file}")


def main() -> None:
    asyncio.run(run_eval())


if __name__ == "__main__":
    main()
