"""Report how the duplicate-detection comments fared once maintainers acted on issues.

Run with: GITHUB_TOKEN=... python .github/scripts/duplicate_detection/duplicate_feedback.py OWNER/REPO
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
from typing import Mapping, TypedDict

from duplicate_comment import MARKER
from issue_corpus import (
    Closure,
    Transport,
    closure_fields,
    fetch_issues,
    is_duplicate,
    post_graphql,
    resolve_canonical,
)

DEFAULT_DAYS = 90
# The header the bot used before the comment carried MARKER.
LEGACY_HEADER = "Potential Duplicate Issue (Semantic Match)"
LEGACY_LABEL = "possible-duplicate"
# GraphQL reports the Actions bot as "github-actions"; REST adds "[bot]".
BOT_LOGINS = {"github-actions", "github-actions[bot]"}

# GraphQL rejects a document with an unused fragment, so each query appends only
# the ones it uses.
COMMENT_PAGE = """
fragment CommentPage on IssueCommentConnection {
  pageInfo {
    hasNextPage
    endCursor
  }
  nodes {
    author {
      login
    }
    body
  }
}
"""

UNLABELED_PAGE = """
fragment UnlabeledPage on IssueTimelineItemsConnection {
  pageInfo {
    hasNextPage
    endCursor
  }
  nodes {
    ... on UnlabeledEvent {
      label {
        name
      }
    }
  }
}
"""

FEEDBACK_QUERY = (
    """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
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
          repository {
            nameWithOwner
          }
        }
        comments(first: 100) {
          ...CommentPage
        }
        timelineItems(first: 100, itemTypes: [UNLABELED_EVENT]) {
          ...UnlabeledPage
        }
      }
    }
  }
}
"""
    + COMMENT_PAGE
    + UNLABELED_PAGE
)

# The rest of an issue's comments or label removals, when one page did not hold them.
MORE_COMMENTS_QUERY = (
    """
query ($id: ID!, $after: String) {
  node(id: $id) {
    ... on Issue {
      comments(first: 100, after: $after) {
        ...CommentPage
      }
    }
  }
}
"""
    + COMMENT_PAGE
)

MORE_UNLABELED_QUERY = (
    """
query ($id: ID!, $after: String) {
  node(id: $id) {
    ... on Issue {
      timelineItems(first: 100, after: $after, itemTypes: [UNLABELED_EVENT]) {
        ...UnlabeledPage
      }
    }
  }
}
"""
    + UNLABELED_PAGE
)

# A primary suggestion is a list item starting with an issue number; references
# inside "(fixed by ...)" or "(also reported as ...)" are not suggestions.
SUGGESTION = re.compile(r"^- #(\d+)", re.MULTILINE)
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


def parse_issue(node: dict, repository: str) -> FeedbackIssue:
    def login(actor: dict | None) -> str:
        # Deleted accounts come back as a null author.
        return actor["login"] if actor else ""

    # The eval pairs hold numbers in this repository only.
    state_reason, duplicate_of = closure_fields(node, repository)
    return {
        "number": node["number"],
        "created_at": node["createdAt"],
        "author": login(node.get("author")),
        "state": node["state"].lower(),
        "state_reason": state_reason,
        "labels": [label["name"] for label in node["labels"]["nodes"]],
        "duplicate_of": duplicate_of,
        "comments": [
            {"author": login(c.get("author")), "body": c["body"]}
            for c in node["comments"]["nodes"]
        ],
        "unlabeled": [
            e["label"]["name"] for e in node["timelineItems"]["nodes"] if e.get("label")
        ],
    }


def remaining_nodes(
    query: str, field: str, issue_id: str, page: dict, token: str, transport: Transport
) -> list[dict]:
    nodes: list[dict] = []
    page_info = page["pageInfo"]
    while page_info["hasNextPage"]:
        variables = {"id": issue_id, "after": page_info["endCursor"]}
        connection = transport(query, variables, token)["node"][field]
        nodes.extend(connection["nodes"])
        page_info = connection["pageInfo"]
    return nodes


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
            for query, field in (
                (MORE_COMMENTS_QUERY, "comments"),
                (MORE_UNLABELED_QUERY, "timelineItems"),
            ):
                node[field]["nodes"] += remaining_nodes(
                    query, field, node["id"], node[field], token, transport
                )
            issues.append(parse_issue(node, repository))
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


def summarise_feedback(
    issues: list[FeedbackIssue], links: Mapping[int, Closure] | None = None
) -> FeedbackReport:
    """links holds every issue's duplicate link, so closures that point at an issue
    which was itself closed as a duplicate resolve the way the detector does."""
    links = links if links is not None else {i["number"]: i for i in issues}
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
        disputed: list[int] = []
        for comment in issue["comments"]:
            # Only the bot's own comment counts; a person may quote it.
            numbers = (
                suggested_numbers(comment["body"])
                if comment["author"] in BOT_LOGINS
                else None
            )
            if numbers is not None:
                commented = True
                suggested = numbers
            elif (
                commented
                and comment["author"] == issue["author"]
                and DISPUTE.search(comment["body"])
            ):
                # Authors often dispute one suggestion and leave the rest alone. A
                # comment naming only other issues disputes none of the suggestions.
                named = {int(n) for n in re.findall(r"#(\d+)", comment["body"])}
                chosen = [n for n in suggested if n in named] if named else suggested
                disputed += [n for n in chosen if n not in disputed]
        if commented:
            report["commented"] += 1
        if disputed:
            report["disputed"].append((issue["number"], disputed))
        if LEGACY_LABEL in issue["unlabeled"]:
            report["label_removed"].append(issue["number"])

        if issue["state"] == "closed" and is_duplicate(issue):
            report["closed_as_duplicate"] += 1
            target = issue["duplicate_of"]
            if target is None:
                continue
            canonical = resolve_canonical(target, links) if target in links else target
            # The detector suggests the canonical issue; older comments suggested
            # whichever issue matched.
            if canonical in suggested or target in suggested:
                report["confirmed"].append(issue["number"])
            else:
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

    token = os.environ["GITHUB_TOKEN"]
    issues = fetch_issues_since(args.repository, token, args.since)
    # Duplicate chains can run through issues opened before the window.
    links = {i["number"]: i for i in fetch_issues(args.repository, token)}
    report = summarise_feedback(issues, links)
    print(render_report(report, args.repository, args.since), end="")


if __name__ == "__main__":
    main()
