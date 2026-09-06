"""Semantic duplicate detection for a newly opened GitHub issue.

Reads {"current": {...}, "others": [...]} from issues_json (written by the
calling workflow via the GitHub API) and writes a ranked list of likely
duplicates to matches_json.

THRESHOLD was empirically calibrated against confirmed duplicate/non-duplicate
issue pairs in AOSSIE-Org/PictoPy: real duplicates scored 0.56-0.85, unrelated
issues (including ones sharing identical issue-template boilerplate) scored
<= 0.31. 0.55 sits in the gap with margin on both sides.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

THRESHOLD = 0.55
MAX_RESULTS = 3


def issue_text(issue: dict) -> str:
    return f"{issue['title']} {issue['body']}".strip()


def dot_product(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def find_duplicates(
    current_embedding: list[float],
    other_embeddings: list[list[float]],
    others: list[dict],
    threshold: float = THRESHOLD,
    max_results: int = MAX_RESULTS,
) -> list[dict]:
    # Embeddings are normalized, so dot product equals cosine similarity.
    matches = []
    for issue, embedding in zip(others, other_embeddings):
        score = dot_product(current_embedding, embedding) * 100
        if score >= threshold * 100:
            matches.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue["url"],
                    "state": issue["state"],
                    "score": round(score, 1),
                }
            )
    matches.sort(key=lambda m: -m["score"])
    return matches[:max_results]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("issues_json", type=Path)
    parser.add_argument("matches_json", type=Path)
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    args = parser.parse_args()

    data = json.loads(args.issues_json.read_text(encoding="utf-8"))
    current = data["current"]
    others = data["others"]

    print(f"Threshold = {args.threshold}")
    print(f"Current issue: #{current['number']}")
    print(f"Candidate issues: {len(others)}")

    if not others:
        args.matches_json.write_text("[]", encoding="utf-8")
        return

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(
        [issue_text(current)] + [issue_text(o) for o in others],
        normalize_embeddings=True,
    ).tolist()

    current_embedding, other_embeddings = embeddings[0], embeddings[1:]

    for issue, embedding in zip(others, other_embeddings):
        score = dot_product(current_embedding, embedding) * 100
        print(f"Issue #{issue['number']} | Score={score:.1f} | Title={issue['title']}")

    matches = find_duplicates(
        current_embedding, other_embeddings, others, args.threshold
    )
    args.matches_json.write_text(json.dumps(matches), encoding="utf-8")


if __name__ == "__main__":
    main()
