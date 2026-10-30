"""Measure retrieval, not vibes.

hit@k  - did the expected source appear in the top k chunks?
decline - for out-of-scope questions, did retrieval correctly return nothing?

Run after ingest.py. Costs one embedding call per question.
"""
from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from retrieve import retrieve  # noqa: E402


def main() -> None:
    # Fail with an explanation rather than a traceback when the project has
    # not been set up yet - this is the first thing anyone cloning it hits.
    try:
        retrieve("smoke test")
    except Exception as exc:
        raise SystemExit(f"Cannot run the evaluation: {exc}")

    cases = yaml.safe_load(
        (pathlib.Path(__file__).parent / "questions.yaml").read_text())

    in_scope = [c for c in cases if c["expect_source"] != "NONE"]
    out_scope = [c for c in cases if c["expect_source"] == "NONE"]

    hits = 0
    print(f"{'result':8} {'expected':14} question")
    print("-" * 72)
    for c in in_scope:
        got = retrieve(c["question"])
        sources = [h["source"] for h in got]
        ok = c["expect_source"] in sources
        hits += ok
        print(f"{'HIT ' if ok else 'MISS':8} {c['expect_source']:14} {c['question']}")
        if not ok:
            print(f"{'':8} returned: {sources or 'nothing'}")

    declined = 0
    for c in out_scope:
        got = retrieve(c["question"])
        ok = len(got) == 0
        declined += ok
        print(f"{'DECLINE' if ok else 'LEAK':8} {'(none)':14} {c['question']}")
        if not ok:
            print(f"{'':8} wrongly returned: {[h['source'] for h in got]}")

    print("-" * 72)
    print(f"hit@k:          {hits}/{len(in_scope)}")
    if out_scope:
        print(f"correct decline: {declined}/{len(out_scope)}")


if __name__ == "__main__":
    main()
