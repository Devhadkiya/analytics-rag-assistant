"""Answer a question from retrieved context, with citations, or decline.

The system prompt is deliberately strict: the model answers only from the
context it is given and says so when the context does not contain the answer.
A self-service analytics assistant that guesses a metric definition is worse
than one that says it does not know, because nobody checks a confident answer.
"""
from __future__ import annotations

import argparse

from openai import OpenAI

from config import CHAT_MODEL, OPENAI_API_KEY
from retrieve import retrieve

SYSTEM = """You answer questions about an analytics handbook.

Rules:
- Use ONLY the numbered context passages provided. Do not use outside knowledge.
- If the passages do not contain the answer, reply exactly:
  "Not covered in the handbook." Then say what is missing.
- Cite the passage numbers you used, like [1] or [2][3], after each claim.
- Be brief. Quote a definition verbatim where one exists."""


def format_context(hits: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] (source: {h['source']}, section: {h['heading'] or '-'})\n{h['text']}"
        for i, h in enumerate(hits, 1))


def answer(question: str) -> dict:
    hits = retrieve(question)
    if not hits:
        return {"answer": "Not covered in the handbook. Nothing in the index "
                          "was close enough to this question to answer from.",
                "hits": []}

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",
             "content": f"Context:\n{format_context(hits)}\n\nQuestion: {question}"},
        ],
    )
    return {"answer": resp.choices[0].message.content.strip(), "hits": hits}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+")
    args = ap.parse_args()

    result = answer(" ".join(args.question))
    print(result["answer"])
    if result["hits"]:
        print("\nRetrieved:")
        for i, h in enumerate(result["hits"], 1):
            print(f"  [{i}] {h['source']} / {h['heading'] or '-'}  "
                  f"(similarity {h['similarity']})")


if __name__ == "__main__":
    main()
