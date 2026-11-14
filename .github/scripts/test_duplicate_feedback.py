"""Run with: python .github/scripts/test_duplicate_feedback.py"""

import json

from duplicate_comment import render_comment
from duplicate_feedback import (
    fetch_issues_since,
    render_report,
    suggested_numbers,
    summarise_feedback,
)

LEGACY_COMMENT = (
    "⚠️ **Potential Duplicate Issue (Semantic Match)**\n\n"
    "1. **Some title** (#799, closed)\n   https://x\n   Similarity: 60.1%\n\n"
    "2. **Other** (#1229, open)\n   https://y\n   Similarity: 58.0%"
)


def new_comment(*numbers: int) -> str:
    matches = [
        {
            "number": n,
            "status": "closed as completed",
            "closed_by": [9000],
            "also_reported_as": [8000],
        }
        for n in numbers
    ]
    body = render_comment(matches)
    assert body is not None
    return body


def make_issue(number: int, comments: list, **fields) -> dict:
    issue = {
        "number": number,
        "created_at": "2026-10-01T00:00:00Z",
        "author": "alice",
        "state": "open",
        "state_reason": None,
        "labels": [],
        "duplicate_of": None,
        "comments": [{"author": a, "body": b} for a, b in comments],
        "unlabeled": [],
    }
    issue.update(fields)
    return issue


def test_suggested_numbers_reads_both_comment_formats() -> None:
    assert suggested_numbers(new_comment(722, 1496)) == [722, 1496]
    assert suggested_numbers(LEGACY_COMMENT) == [799, 1229]
    assert suggested_numbers("Thanks for opening this issue!") is None


def test_suggested_numbers_reads_cross_repository_references() -> None:
    body = render_comment(
        [{"number": 5, "status": "open", "closed_by": [], "also_reported_as": [6]}],
        "o/r",
    )
    assert body is not None
    assert suggested_numbers(body) == [5]


def test_summarise_feedback_counts_outcomes() -> None:
    bot = "github-actions"
    issues = [
        # Suggestion confirmed: closed as a duplicate of a suggested issue.
        make_issue(
            10,
            [(bot, new_comment(3, 4))],
            state="closed",
            state_reason="duplicate",
            duplicate_of=4,
        ),
        # Missed: closed as a duplicate of an issue the bot did not suggest.
        make_issue(
            11,
            [(bot, new_comment(3))],
            state="closed",
            state_reason="duplicate",
            duplicate_of=7,
        ),
        # Disputed by the author, and the legacy label removed by hand.
        make_issue(
            12,
            [(bot, LEGACY_COMMENT), ("alice", "This is not a duplicate of #799.")],
            unlabeled=["possible-duplicate"],
        ),
        # Someone else saying "not a duplicate" is not the author disputing it.
        make_issue(13, [(bot, new_comment(3)), ("bob", "Not a duplicate, I think")]),
        # No bot comment at all.
        make_issue(14, [("alice", "Any update?")]),
    ]

    report = summarise_feedback(issues)

    assert report["issues"] == 5
    assert report["commented"] == 4
    assert report["closed_as_duplicate"] == 2
    assert report["confirmed"] == [10]
    assert report["missed"] == [(11, 7)]
    assert report["disputed"] == [(12, [799])]
    assert report["label_removed"] == [12]


def test_dispute_naming_one_suggestion_only_counts_that_one() -> None:
    issue = make_issue(
        20,
        [
            ("github-actions", new_comment(1684, 1576, 1633)),
            ("alice", "This isn't a duplicate of #1684, it is about timing."),
        ],
    )
    assert summarise_feedback([issue])["disputed"] == [(20, [1684])]


def test_fetch_issues_since_stops_at_the_cutoff() -> None:
    def node(number: int, created: str) -> dict:
        return {
            "number": number,
            "createdAt": created,
            "state": "OPEN",
            "stateReason": None,
            "author": None,
            "labels": {"nodes": []},
            "duplicateOf": None,
            "comments": {"nodes": [{"author": None, "body": "hi"}]},
            "timelineItems": {"nodes": [{"label": {"name": "possible-duplicate"}}]},
        }

    pages = {
        None: ([node(30, "2026-11-01T00:00:00Z")], True, "c1"),
        "c1": (
            [node(29, "2026-10-02T00:00:00Z"), node(28, "2026-09-01T00:00:00Z")],
            True,
            "c2",
        ),
    }
    calls = []

    def transport(query: str, variables: dict, token: str) -> dict:
        calls.append(variables["after"])
        nodes, has_next, cursor = pages[variables["after"]]
        return {
            "repository": {
                "issues": {
                    "nodes": nodes,
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                }
            }
        }

    issues = fetch_issues_since("o/r", "tok", "2026-10-01", transport)

    assert [i["number"] for i in issues] == [30, 29]
    assert calls == [None, "c1"]
    assert issues[0]["author"] == ""
    assert issues[0]["unlabeled"] == ["possible-duplicate"]


def test_render_report_prints_pairs_ready_for_the_eval_file() -> None:
    report = {
        "issues": 10,
        "commented": 2,
        "closed_as_duplicate": 2,
        "confirmed": [10],
        "missed": [(11, 7)],
        "disputed": [(12, [799])],
        "label_removed": [],
    }
    text = render_report(report, "o/r", "2026-08-01")

    assert "| Issues the bot commented on | 2 | 20% of issues |" in text
    assert "| 1 | 50% of duplicate closures |" in text
    assert "n/a" not in render_report({**report, "closed_as_duplicate": 0}, "o/r", "x")
    lines = [line.rstrip(",") for line in text.splitlines() if line.startswith("{")]
    entries = [json.loads(line) for line in lines]
    assert {"issue": 11, "candidate": 7} in [
        {k: e[k] for k in ("issue", "candidate")} for e in entries
    ]
    assert {"issue": 12, "candidate": 799, "source": "author-disputed"} in entries


if __name__ == "__main__":
    test_suggested_numbers_reads_both_comment_formats()
    test_suggested_numbers_reads_cross_repository_references()
    test_summarise_feedback_counts_outcomes()
    test_dispute_naming_one_suggestion_only_counts_that_one()
    test_fetch_issues_since_stops_at_the_cutoff()
    test_render_report_prints_pairs_ready_for_the_eval_file()
    print("All tests passed.")
