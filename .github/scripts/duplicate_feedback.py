"""Report how the duplicate-detection comments fared once maintainers acted on issues.

Run with: GITHUB_TOKEN=... python .github/scripts/duplicate_feedback.py OWNER/REPO
          [--since YYYY-MM-DD]

Prints a Markdown report: how often the bot commented, how often a suggestion was
confirmed by a duplicate closure, which duplicates it missed, and which suggestions
authors disputed. The last two print as entries ready for duplicate_eval_pairs.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from duplicate_comment import MARKER
from issue_corpus import Transport, is_duplicate, post_graphql

DEFAULT_DAYS = 90
# The header the bot used before the comment carried MARKER.
LEGACY_HEADER = "Potential Duplicate Issue (Semantic Match)"
LEGACY_LABEL = "possible-duplicate"

FEEDBACK_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        createdAt
        state
        stateReason
        author {
          login
        }
        labels(first: 20) {
          nodes {
            name
          }
        }
        duplicateOf {
          number
        }
        comments(first: 50) {
          nodes {
            author {
              login
            }
            body
          }
        }
        timelineItems(first: 20, itemTypes: [UNLABELED_EVENT]) {
          nodes {
            ... on UnlabeledEvent {
              label {
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

# A primary suggestion is a list item starting with an issue reference; references
# inside "(fixed by ...)" or "(also reported as ...)" are not suggestions.
SUGGESTION = re.compile(r"^- (?:[\w.-]+/[\w.-]+)?#(\d+)", re.MULTILINE)
LEGACY_SUGGESTION = re.compile(r"\(#(\d+), ")
DISPUTE = re.compile(
    r"not (?:a )?duplicate|isn't a duplicate|is not the same|different issue"
    r"|distinct from",
    re.IGNORECASE,
)


class Comment(TypedDict):
    author: str
    body: str


class FeedbackIssue(TypedDict):
    number: int
    created_at: str
    author: str
    state: str
    state_reason: str | None
    labels: list[str]
    duplicate_of: int | None
    comments: list[Comment]
    unlabeled: list[str]


class FeedbackReport(TypedDict):
    issues: int
    commented: int
    closed_as_duplicate: int
    confirmed: list[int]
    missed: list[tuple[int, int]]
    disputed: list[tuple[int, list[int]]]
    label_removed: list[int]


def parse_issue(node: dict) -> FeedbackIssue:
    def login(actor: dict | None) -> str:
        # Deleted accounts come back as a null author.
        return actor["login"] if actor else ""

    reason = node.get("stateReason")
    duplicate_of = node.get("duplicateOf")
    return {
        "number": node["number"],
        "created_at": node["createdAt"],
        "author": login(node.get("author")),
        "state": node["state"].lower(),
        "state_reason": reason.lower() if reason else None,
        "labels": [label["name"] for label in node["labels"]["nodes"]],
        "duplicate_of": duplicate_of["number"] if duplicate_of else None,
        "comments": [
            {"author": login(c.get("author")), "body": c["body"]}
            for c in node["comments"]["nodes"]
        ],
        "unlabeled": [
            e["label"]["name"] for e in node["timelineItems"]["nodes"] if e.get("label")
        ],
    }


def fetch_issues_since(
    repository: str, token: str, since: str, transport: Transport = post_graphql
) -> list[FeedbackIssue]:
    """Issues created on or after since (ISO date), newest first."""
    owner, name = repository.split("/", 1)
    issues: list[FeedbackIssue] = []
    after: str | None = None
    while True:
        variables = {"owner": owner, "name": name, "after": after}
        data = transport(FEEDBACK_QUERY, variables, token)
        connection = data["repository"]["issues"]
        for node in connection["nodes"]:
            if node["createdAt"] < since:
                return issues
            issues.append(parse_issue(node))
        if not connection["pageInfo"]["hasNextPage"]:
            return issues
        after = connection["pageInfo"]["endCursor"]


def suggested_numbers(body: str) -> list[int] | None:
    """Issue numbers the bot suggested, or None if body is not a bot suggestion."""
    if MARKER in body:
        return [int(n) for n in SUGGESTION.findall(body)]
    if LEGACY_HEADER in body:
        return [int(n) for n in LEGACY_SUGGESTION.findall(body)]
    return None


def summarise_feedback(issues: list[FeedbackIssue]) -> FeedbackReport:
    report: FeedbackReport = {
        "issues": len(issues),
        "commented": 0,
        "closed_as_duplicate": 0,
        "confirmed": [],
        "missed": [],
        "disputed": [],
        "label_removed": [],
    }
    for issue in issues:
        suggested: list[int] = []
        commented = False
        disputed: list[int] | None = None
        for comment in issue["comments"]:
            numbers = suggested_numbers(comment["body"])
            if numbers is not None:
                commented = True
                suggested = numbers
            elif (
                commented
                and comment["author"] == issue["author"]
                and DISPUTE.search(comment["body"])
            ):
                # Authors often dispute one suggestion and leave the rest alone.
                named = [int(n) for n in re.findall(r"#(\d+)", comment["body"])]
                disputed = [n for n in suggested if n in named] or suggested
        if commented:
            report["commented"] += 1
        if disputed is not None:
            report["disputed"].append((issue["number"], disputed))
        if LEGACY_LABEL in issue["unlabeled"]:
            report["label_removed"].append(issue["number"])

        if issue["state"] == "closed" and is_duplicate(issue):
            report["closed_as_duplicate"] += 1
            canonical = issue["duplicate_of"]
            if canonical is not None and canonical in suggested:
                report["confirmed"].append(issue["number"])
            elif canonical is not None:
                report["missed"].append((issue["number"], canonical))
    return report


def render_report(report: FeedbackReport, repository: str, since: str) -> str:
    def share(part: int, whole: int, unit: str) -> str:
        return f"{part / whole:.0%} of {unit}" if whole else ""

    commented = report["commented"]
    closures = report["closed_as_duplicate"]
    lines = [
        f"## Duplicate detection feedback for {repository}",
        "",
        f"Issues opened since {since}: {report['issues']}.",
        "",
        "| Measure | Count | Share |",
        "| --- | --- | --- |",
        f"| Issues the bot commented on | {commented} | "
        f"{share(commented, report['issues'], 'issues')} |",
        f"| Suggestion confirmed by a duplicate closure | {len(report['confirmed'])} | "
        f"{share(len(report['confirmed']), commented, 'comments')} |",
        f"| Suggestion disputed by the issue author | {len(report['disputed'])} | "
        f"{share(len(report['disputed']), commented, 'comments')} |",
        f"| `{LEGACY_LABEL}` label removed by hand | {len(report['label_removed'])} | |",
        f"| Closed as duplicate | {closures} | |",
        f"| Closed as duplicate, but the bot missed the original | "
        f"{len(report['missed'])} | "
        f"{share(len(report['missed']), closures, 'duplicate closures')} |",
    ]
    # Ready to paste into duplicate_eval_pairs.json; the kind needs a human look.
    if report["missed"]:
        lines += [
            "",
            "### Missed duplicates",
            "",
            "Add to `positives`, changing `kind` to `covered-by-umbrella` where a "
            "narrow issue was folded into a broader one:",
            "",
            "```json",
        ]
        lines += [
            json.dumps(
                {
                    "issue": issue,
                    "candidate": canonical,
                    "kind": "same-report",
                    "source": "github-duplicate",
                }
            )
            + ","
            for issue, canonical in report["missed"]
        ]
        lines += ["```"]
    if report["disputed"]:
        lines += [
            "",
            "### Disputed suggestions",
            "",
            "Add to `negatives`:",
            "",
            "```json",
        ]
        lines += [
            json.dumps(
                {"issue": issue, "candidate": candidate, "source": "author-disputed"}
            )
            + ","
            for issue, suggested in report["disputed"]
            for candidate in suggested
        ]
        lines += ["```"]
    return "\n".join(lines) + "\n"


def main() -> None:
    default_since = datetime.now(timezone.utc) - timedelta(days=DEFAULT_DAYS)
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", help="OWNER/REPO")
    parser.add_argument("--since", default=default_since.strftime("%Y-%m-%d"))
    args = parser.parse_args()

    issues = fetch_issues_since(args.repository, os.environ["GITHUB_TOKEN"], args.since)
    report = summarise_feedback(issues)
    print(render_report(report, args.repository, args.since), end="")


if __name__ == "__main__":
    main()
