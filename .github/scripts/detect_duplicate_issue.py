"""Semantic duplicate detection for a newly opened or retitled GitHub issue.

Reads the issue corpus written by issue_corpus.py and the issue from the workflow's
event payload, writes the ranked matches to matches_json, and writes the comment to
post to comment_md (empty when there is nothing to suggest).

Titles carry most of the signal: on the labelled pairs, long bodies pulled unrelated
issues together, so the body only counts when it is a very close match. Measure any change to the text, model, threshold or ranking with
eval_duplicate_detection.py before shipping it; see README.md in this directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from duplicate_comment import render_comment
from issue_corpus import clean_title, issue_text, resolve_canonical, status

# Together these flagged 16% of 2026 issues, showed 36% of labelled duplicates, and
# showed none of the labelled non-duplicates.
TITLE_THRESHOLD = 0.70
BODY_THRESHOLD = 0.80
MAX_RESULTS = 3
MODEL_NAME = "all-MiniLM-L6-v2"


def title_text(issue: dict) -> str:
    return clean_title(issue["title"])


def dot_product(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def find_duplicates(
    title_scores: list[float],
    body_scores: list[float],
    others: list[dict],
    title_threshold: float = TITLE_THRESHOLD,
    body_threshold: float = BODY_THRESHOLD,
    max_results: int = MAX_RESULTS,
) -> list[dict]:
    """Rank others[i] by its title and title-plus-body similarity, on a 0-1 scale."""
    by_number = {issue["number"]: issue for issue in others}
    # A match on an issue closed as a duplicate counts for the issue it duplicates,
    # so authors are pointed at the discussion that was kept.
    best: dict[int, float] = {}
    reported_as: dict[int, list[int]] = {}
    for issue, title_score, body_score in zip(others, title_scores, body_scores):
        if title_score < title_threshold and body_score < body_threshold:
            continue
        score = max(title_score, body_score)
        target = resolve_canonical(issue["number"], by_number)
        if target != issue["number"]:
            reported_as.setdefault(target, []).append(issue["number"])
        best[target] = max(score, best.get(target, score))

    ranked = sorted(best, key=lambda number: -best[number])[:max_results]
    return [
        {
            "number": number,
            "title": by_number[number]["title"],
            "status": status(by_number[number]),
            "closed_by": by_number[number]["closed_by"],
            "also_reported_as": sorted(reported_as.get(number, [])),
            "score": round(best[number], 3),
        }
        for number in ranked
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_json", type=Path, help="written by issue_corpus.py")
    parser.add_argument("event_json", type=Path, help="the issues event payload")
    parser.add_argument("matches_json", type=Path)
    parser.add_argument("comment_md", type=Path)
    args = parser.parse_args()

    corpus = json.loads(args.corpus_json.read_text(encoding="utf-8"))
    current = json.loads(args.event_json.read_text(encoding="utf-8"))["issue"]
    # Issues opened after this one cannot be what it duplicates.
    others = [issue for issue in corpus if issue["number"] < current["number"]]

    print(f"Thresholds: title {TITLE_THRESHOLD}, body {BODY_THRESHOLD}")
    print(f"Current issue: #{current['number']}")
    print(f"Candidate issues: {len(others)}")

    matches: list[dict] = []
    if others:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(MODEL_NAME)

        def similarities(to_text: Callable[[dict], str]) -> list[float]:
            embeddings = model.encode(
                [to_text(current)] + [to_text(o) for o in others],
                normalize_embeddings=True,
            ).tolist()
            # Embeddings are normalized, so dot product equals cosine similarity.
            return [dot_product(embeddings[0], e) for e in embeddings[1:]]

        title_scores = similarities(title_text)
        body_scores = similarities(issue_text)
        for issue, t, b in zip(others, title_scores, body_scores):
            print(f"#{issue['number']} | title={t:.3f} body={b:.3f} | {issue['title']}")
        matches = find_duplicates(title_scores, body_scores, others)

    args.matches_json.write_text(json.dumps(matches), encoding="utf-8")
    args.comment_md.write_text(render_comment(matches) or "", encoding="utf-8")


if __name__ == "__main__":
    main()
