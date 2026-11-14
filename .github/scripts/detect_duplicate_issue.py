"""Semantic duplicate detection for a newly opened GitHub issue.

Reads the issue corpus written by issue_corpus.py and the issue from the workflow's
event payload, and writes a ranked list of likely duplicates to matches_json.

Measure any change to the text, model, threshold or ranking with
eval_duplicate_detection.py before shipping it; see README.md in this directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from issue_corpus import issue_text, resolve_canonical, status

THRESHOLD = 0.55
MAX_RESULTS = 3
MODEL_NAME = "all-MiniLM-L6-v2"


def dot_product(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def find_duplicates(
    current_embedding: list[float],
    other_embeddings: list[list[float]],
    others: list[dict],
    threshold: float = THRESHOLD,
    max_results: int = MAX_RESULTS,
) -> list[dict]:
    by_number = {issue["number"]: issue for issue in others}
    # A match on an issue closed as a duplicate counts for the issue it duplicates,
    # so authors are pointed at the discussion that was kept.
    scores: dict[int, float] = {}
    reported_as: dict[int, list[int]] = {}
    for issue, embedding in zip(others, other_embeddings):
        # Embeddings are normalized, so dot product equals cosine similarity.
        score = dot_product(current_embedding, embedding) * 100
        if score < threshold * 100:
            continue
        target = resolve_canonical(issue["number"], by_number)
        if target != issue["number"]:
            reported_as.setdefault(target, []).append(issue["number"])
        scores[target] = max(score, scores.get(target, score))

    # Sort by the raw score, not the rounded display value, so close scores
    # that round to the same tenth (e.g. 90.04 vs 90.01) still rank correctly.
    ranked = sorted(scores, key=lambda number: -scores[number])[:max_results]
    return [
        {
            "number": number,
            "title": by_number[number]["title"],
            "url": by_number[number]["url"],
            "status": status(by_number[number]),
            "score": round(scores[number], 1),
            "also_reported_as": sorted(reported_as.get(number, [])),
        }
        for number in ranked
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_json", type=Path, help="written by issue_corpus.py")
    parser.add_argument("event_json", type=Path, help="the issues event payload")
    parser.add_argument("matches_json", type=Path)
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    args = parser.parse_args()

    corpus = json.loads(args.corpus_json.read_text(encoding="utf-8"))
    current = json.loads(args.event_json.read_text(encoding="utf-8"))["issue"]
    others = [issue for issue in corpus if issue["number"] != current["number"]]

    print(f"Threshold = {args.threshold}")
    print(f"Current issue: #{current['number']}")
    print(f"Candidate issues: {len(others)}")

    if not others:
        args.matches_json.write_text("[]", encoding="utf-8")
        return

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
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
