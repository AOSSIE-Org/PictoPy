"""Semantic duplicate detection for a newly opened or retitled GitHub issue.

Reads the issue corpus written by issue_corpus.py and the issue from the workflow's
event payload, writes the ranked matches to matches_json, and writes the comment to
post to comment_md (empty when there is nothing to suggest).

Titles carry most of the signal: on the labelled pairs, long bodies pulled unrelated
issues together, so the body only counts when it is a very close match. Measure any
change to the text, model, threshold or ranking with eval_duplicate_detection.py
before shipping it; see README.md in this directory.
"""

from __future__ import annotations

import argparse
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Mapping

from duplicate_comment import render_comment
from issue_corpus import (
    Issue,
    clean_title,
    is_tracking,
    issue_text,
    resolve_canonical,
    status,
)

# Together these flagged 16% of 2026 issues, showed 36% of labelled duplicates, and
# showed none of the labelled non-duplicates.
TITLE_THRESHOLD = 0.70
BODY_THRESHOLD = 0.80
MAX_RESULTS = 3
# Narrower issues are often folded into a tracking issue whose text differs a lot
# (a logout button into "Settings UI"), so tracking issues get a lower bar and their
# own section. Against a stand-in set of tracking issues, this pointed 8% of 2026
# issues at one, and showed none of the labelled non-duplicates.
TRACKING_TITLE_THRESHOLD = 0.50
TRACKING_BODY_THRESHOLD = 0.60
MAX_TRACKING_RESULTS = 1
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# fastembed's ONNX export of MODEL_NAME, which scores identically to the PyTorch model
# without installing torch. Pinned so the thresholds above stay calibrated.
MODEL_REPO = "Qdrant/all-MiniLM-L6-v2-onnx"
MODEL_REVISION = "d13954661f83248295ba75c1ed411eef3b7b936e"


def title_text(issue: Mapping[str, Any]) -> str:
    return clean_title(issue["title"])


def dot_product(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@lru_cache(maxsize=1)
def _load_model() -> Any:
    from fastembed import TextEmbedding
    from huggingface_hub import snapshot_download

    path = snapshot_download(MODEL_REPO, revision=MODEL_REVISION)
    return TextEmbedding(MODEL_NAME, specific_model_path=path)


def embed(texts: list[str]) -> list[list[float]]:
    """Unit-length embeddings, so a dot product is a cosine similarity."""
    vectors = [vector.tolist() for vector in _load_model().embed(texts)]
    return [[x / math.sqrt(dot_product(v, v)) for x in v] for v in vectors]


def find_duplicates(
    title_scores: list[float],
    body_scores: list[float],
    others: list[Issue],
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
        tracking = is_tracking(issue)
        title_min = TRACKING_TITLE_THRESHOLD if tracking else title_threshold
        body_min = TRACKING_BODY_THRESHOLD if tracking else body_threshold
        if title_score < title_min and body_score < body_min:
            continue
        score = max(title_score, body_score)
        target = resolve_canonical(issue["number"], by_number)
        if target != issue["number"]:
            reported_as.setdefault(target, []).append(issue["number"])
        best[target] = max(score, best.get(target, score))

    ranked = sorted(best, key=lambda number: -best[number])
    tracked = [n for n in ranked if is_tracking(by_number[n])]
    others_ranked = [n for n in ranked if not is_tracking(by_number[n])]
    ranked = tracked[:MAX_TRACKING_RESULTS] + others_ranked[:max_results]
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


def candidates(corpus: list[Issue], current: dict) -> list[Issue]:
    # Issues opened after this one cannot be what it duplicates.
    return [issue for issue in corpus if issue["created_at"] < current["created_at"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_json", type=Path, help="written by issue_corpus.py")
    parser.add_argument("event_json", type=Path, help="the issues event payload")
    parser.add_argument("matches_json", type=Path)
    parser.add_argument("comment_md", type=Path)
    args = parser.parse_args()

    corpus = json.loads(args.corpus_json.read_text(encoding="utf-8"))
    event = json.loads(args.event_json.read_text(encoding="utf-8"))
    current = event["issue"]
    others = candidates(corpus, current)

    print(f"Thresholds: title {TITLE_THRESHOLD}, body {BODY_THRESHOLD}")
    print(f"Current issue: #{current['number']}")
    print(f"Candidate issues: {len(others)}")

    matches: list[dict] = []
    if others:

        def similarities(to_text: Callable[[Mapping[str, Any]], str]) -> list[float]:
            embeddings = embed([to_text(current)] + [to_text(o) for o in others])
            return [dot_product(embeddings[0], e) for e in embeddings[1:]]

        title_scores = similarities(title_text)
        body_scores = similarities(issue_text)
        for issue, t, b in zip(others, title_scores, body_scores):
            print(f"#{issue['number']} | title={t:.3f} body={b:.3f} | {issue['title']}")
        matches = find_duplicates(title_scores, body_scores, others)

    args.matches_json.write_text(json.dumps(matches), encoding="utf-8")
    comment = render_comment(matches)
    args.comment_md.write_text(comment or "", encoding="utf-8")


if __name__ == "__main__":
    main()
