"""Offline evaluation of duplicate issue detection against labelled issue pairs.

Replays the detector over a snapshot of the repository's issues. Each query issue is
compared only with older issues, as it would have been on the day it was opened.

Run with: python .github/scripts/eval_duplicate_detection.py [--refresh] [--json out]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, Sequence, TypedDict

import detect_duplicate_issue as detector
from issue_corpus import TRACKING_LABEL, issue_text

HERE = Path(__file__).parent
PAIRS_PATH = HERE / "duplicate_eval_pairs.json"
CACHE_DIR = HERE / ".duplicate_eval_cache"
DEFAULT_SINCE = "2026-01-01"
FIXED_THRESHOLDS = (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85)
FLAG_RATES = (0.05, 0.10, 0.20)
GATE_TITLE_MINS = (0.60, 0.65, 0.70)
GATE_BODY_MINS = (0.55, 0.65, 0.75)


class Issue(TypedDict):
    number: int
    title: str
    body: str
    created_at: str
    state: str
    state_reason: str | None
    url: str
    labels: list[str]
    duplicate_of: int | None
    closed_by: list[int]


class Pair(TypedDict, total=False):
    issue: int
    candidate: int
    source: str
    kind: str  # positives only


class Outcome(TypedDict):
    flag_rate: float
    positives_shown: float
    negatives_shown: float


def next_link(link_header: str) -> str | None:
    # REST page numbers stop at page 10 for large repos; the Link cursor does not.
    match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
    return match.group(1) if match else None


def fetch_issues(repository: str, token: str | None) -> list[Issue]:
    # REST rather than issue_corpus's GraphQL fetch, so the harness runs without a
    # token. REST has no duplicate links, so duplicates are scored as themselves.
    url: str | None = (
        f"https://api.github.com/repos/{repository}/issues?state=all&per_page=100"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "duplicate-detection-eval",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    issues: list[Issue] = []
    while url:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            page = json.loads(response.read().decode("utf-8"))
            url = next_link(response.headers.get("Link", ""))
        for item in page:
            if "pull_request" in item:
                continue
            issues.append(
                {
                    "number": item["number"],
                    "title": item["title"],
                    "body": item["body"] or "",
                    "created_at": item["created_at"],
                    "state": item["state"],
                    "state_reason": item.get("state_reason"),
                    "url": item["html_url"],
                    "labels": [label["name"] for label in item["labels"]],
                    "duplicate_of": None,
                    "closed_by": [],
                }
            )
    return sorted(issues, key=lambda i: i["number"])


def load_corpus(repository: str, refresh: bool) -> list[Issue]:
    path = CACHE_DIR / "issues_v2.json"
    if refresh or not path.exists():
        print(f"Fetching issues from {repository}...", file=sys.stderr)
        issues = fetch_issues(repository, os.environ.get("GITHUB_TOKEN"))
        CACHE_DIR.mkdir(exist_ok=True)
        path.write_text(json.dumps(issues), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def load_pairs(path: Path = PAIRS_PATH) -> tuple[str, list[Pair], list[Pair]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["repository"], data["positives"], data["negatives"]


# "title" and "body" are the two texts the detector scores; "raw" is the uncleaned
# title and body the detector used before.
VARIANTS: dict[str, Callable[[Issue], str]] = {
    "title": lambda i: detector.title_text(dict(i)),
    "body": lambda i: issue_text(dict(i)),
    "raw": lambda i: f"{i['title']} {i['body']}".strip(),
}


def similarity_rows(texts: list[str]) -> list[list[float]]:
    import numpy as np

    model_id = [detector.MODEL_REPO, detector.MODEL_REVISION]
    digest = hashlib.sha1("\x00".join(model_id + texts).encode("utf-8")).hexdigest()
    path = CACHE_DIR / f"embeddings_{digest[:16]}.npy"
    if path.exists():
        embeddings = np.load(path)
    else:
        embeddings = np.array(detector.embed(texts), dtype=np.float32)
        CACHE_DIR.mkdir(exist_ok=True)
        np.save(path, embeddings)
    return (embeddings @ embeddings.T).tolist()


def percentile(values: Sequence[float], pct: float) -> float:
    # Linear interpolation between closest ranks, the same as numpy's default.
    ordered = sorted(values)
    position = (len(ordered) - 1) * pct / 100
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def rank_of(scores: Sequence[float], index: int) -> int:
    return 1 + sum(1 for s in scores if s > scores[index])


def top_matches(
    rank_scores: Sequence[float],
    gates: Iterable[tuple[Sequence[float], float]],
    max_results: int = detector.MAX_RESULTS,
) -> list[int]:
    """Indices that pass every (scores, minimum) gate, best rank_scores first."""
    gates = list(gates)
    kept = [
        j
        for j in range(len(rank_scores))
        if all(scores[j] >= minimum for scores, minimum in gates)
    ]
    kept.sort(key=lambda j: -rank_scores[j])
    return kept[:max_results]


def summarise(
    shown: dict[int, list[int]],
    eval_queries: Sequence[int],
    positives: Sequence[Pair],
    negatives: Sequence[Pair],
) -> Outcome:
    def share(pairs: Sequence[Pair]) -> float:
        hits = sum(1 for p in pairs if p["candidate"] in shown[p["issue"]])
        return hits / len(pairs) if pairs else 0.0

    flagged = sum(1 for q in eval_queries if shown[q])
    return {
        "flag_rate": flagged / len(eval_queries) if eval_queries else 0.0,
        "positives_shown": share(positives),
        "negatives_shown": share(negatives),
    }


def usable_pairs(
    pairs: Sequence[Pair], position: dict[int, int], label: str
) -> list[Pair]:
    usable = []
    for pair in pairs:
        issue, candidate = pair["issue"], pair["candidate"]
        if issue not in position or candidate not in position:
            print(f"skipping {label} #{issue} -> #{candidate}: not an issue in corpus")
        elif candidate > issue:
            print(f"skipping {label} #{issue} -> #{candidate}: candidate is newer")
        else:
            usable.append(pair)
    return usable


def evaluate(
    corpus: list[Issue], positives: list[Pair], negatives: list[Pair], since: str
) -> dict:
    numbers = [i["number"] for i in corpus]
    position = {n: k for k, n in enumerate(numbers)}
    positives = usable_pairs(positives, position, "positive")
    negatives = usable_pairs(negatives, position, "negative")
    eval_queries = [
        i["number"]
        for i in corpus
        if i["created_at"] >= since and position[i["number"]]
    ]
    queries = sorted(set(eval_queries) | {p["issue"] for p in positives + negatives})

    # Row q holds similarities to older issues only, indexed like `numbers`.
    rows: dict[str, dict[int, list[float]]] = {}
    for name, to_text in VARIANTS.items():
        print(f"Embedding corpus for variant '{name}'...", file=sys.stderr)
        sim = similarity_rows([to_text(i) for i in corpus])
        rows[name] = {q: sim[position[q]][: position[q]] for q in queries}

    def run(variant: str, threshold: float) -> Outcome:
        shown = {
            q: [numbers[j] for j in top_matches(r, [(r, threshold)])]
            for q, r in rows[variant].items()
        }
        return summarise(shown, eval_queries, positives, negatives)

    # The detector's own selection, so the headline number is what ships.
    shipped = {
        q: [
            m["number"]
            for m in detector.find_duplicates(
                rows["title"][q], rows["body"][q], list(corpus[: position[q]])
            )
        ]
        for q in queries
    }
    results: dict = {
        "eval_queries": len(eval_queries),
        "since": since,
        "positives": len(positives),
        "negatives": len(negatives),
        "detector": summarise(shipped, eval_queries, positives, negatives),
        "detector_by_kind": {
            kind: summarise(
                shipped, eval_queries, [p for p in positives if p["kind"] == kind], []
            )["positives_shown"]
            for kind in sorted({p["kind"] for p in positives})
        },
        "variants": {},
    }
    for name, variant_rows in rows.items():
        pos_scores = [
            variant_rows[p["issue"]][position[p["candidate"]]] for p in positives
        ]
        pos_ranks = [
            rank_of(variant_rows[p["issue"]], position[p["candidate"]])
            for p in positives
        ]
        neg_scores = [
            variant_rows[p["issue"]][position[p["candidate"]]] for p in negatives
        ]
        # Thresholds that flag a fixed share of issues compare variants fairly even
        # when their score scales differ.
        top1 = [max(variant_rows[q]) for q in eval_queries]
        equal_flag_rate = {}
        for rate in FLAG_RATES:
            threshold = percentile(top1, 100 * (1 - rate))
            equal_flag_rate[f"{rate:.2f}"] = {
                "threshold": threshold,
                **run(name, threshold),
            }
        k = detector.MAX_RESULTS
        results["variants"][name] = {
            "recall_at_1": sum(r <= 1 for r in pos_ranks) / len(pos_ranks),
            f"recall_at_{k}": sum(r <= k for r in pos_ranks) / len(pos_ranks),
            "positive_score_median": percentile(pos_scores, 50),
            "negative_score_median": percentile(neg_scores, 50),
            "fixed_thresholds": {f"{t:.2f}": run(name, t) for t in FIXED_THRESHOLDS},
            "equal_flag_rate": equal_flag_rate,
        }

    gates = {}
    for title_min in GATE_TITLE_MINS:
        for body_min in GATE_BODY_MINS:
            shown = {
                q: [
                    numbers[j]
                    for j in top_matches(
                        rows["title"][q],
                        [
                            (rows["title"][q], title_min),
                            (rows["body"][q], body_min),
                        ],
                    )
                ]
                for q in queries
            }
            gates[f"title>={title_min:.2f} and body>={body_min:.2f}"] = summarise(
                shown, eval_queries, positives, negatives
            )
    results["gates"] = gates
    return results


def row(label: str, o: Outcome) -> str:
    return (
        f"  {label:<38} flagged {o['flag_rate']:6.1%}   "
        f"duplicates shown {o['positives_shown']:5.0%}   "
        f"hard negatives shown {o['negatives_shown']:5.0%}"
    )


def print_report(results: dict) -> None:
    k = detector.MAX_RESULTS
    print(
        f"\nQueries: {results['eval_queries']} issues created since {results['since']}; "
        f"{results['positives']} duplicate pairs, {results['negatives']} hard negatives."
    )
    print(
        f"A pair counts as shown when the candidate is in the top {k} and passes the "
        "threshold or gate.\n"
    )
    print(row("DETECTOR AS SHIPPED", results["detector"]))
    by_kind = ", ".join(f"{k} {v:.0%}" for k, v in results["detector_by_kind"].items())
    print(f"  {'':<38} duplicates shown by kind: {by_kind}")
    print()

    for name, v in results["variants"].items():
        print(
            f"== {name}: recall@1 {v['recall_at_1']:.2f}, recall@{k} "
            f"{v[f'recall_at_{k}']:.2f}; median score duplicates "
            f"{v['positive_score_median']:.2f}, hard negatives "
            f"{v['negative_score_median']:.2f}"
        )
        for t, o in v["fixed_thresholds"].items():
            print(row(f"threshold {t}", o))
        for rate, o in v["equal_flag_rate"].items():
            print(
                row(f"target flag rate {float(rate):.0%} (t={o['threshold']:.2f})", o)
            )
        print()
    print("== combined gate (ranked by title score)")
    for label, o in results["gates"].items():
        print(row(label, o))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=DEFAULT_SINCE, help="eval window start")
    parser.add_argument("--refresh", action="store_true", help="re-fetch issues")
    parser.add_argument("--json", type=Path, help="also write results here")
    parser.add_argument(
        "--assume-tracking",
        default="",
        help=f"comma-separated issue numbers to treat as labelled {TRACKING_LABEL!r}",
    )
    args = parser.parse_args()

    repository, positives, negatives = load_pairs()
    corpus = load_corpus(repository, args.refresh)
    # Lets maintainers measure a proposed set of tracking issues before labelling.
    assumed = {int(n) for n in args.assume_tracking.split(",") if n.strip()}
    for issue in corpus:
        if issue["number"] in assumed:
            issue["labels"] = [*issue["labels"], TRACKING_LABEL]
    results = evaluate(corpus, positives, negatives, args.since)
    print_report(results)
    if args.json:
        args.json.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
