"""Fetch and normalise a repository's issues for duplicate detection.

Run with: GITHUB_TOKEN=... python .github/scripts/issue_corpus.py OWNER/REPO out.json

Uses only the standard library, so the workflow can fetch issues with a token before
it installs any third-party packages.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Callable, TypedDict

GRAPHQL_URL = "https://api.github.com/graphql"
# Chains like #700 -> #693 -> #638 exist; the cap stops a malformed chain early.
MAX_DUPLICATE_DEPTH = 5

# The issues connection never returns pull requests, unlike the REST issues list.
ISSUES_QUERY = """
query ($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        url
        state
        stateReason
        createdAt
        labels(first: 20) {
          nodes {
            name
          }
        }
        duplicateOf {
          number
        }
        closedByPullRequestsReferences(first: 5, includeClosedPrs: true) {
          nodes {
            number
            merged
          }
        }
      }
    }
  }
}
"""

# Issue-template scaffolding shared by every issue of a type; it inflates similarity
# between unrelated issues. Patterns follow .github/ISSUE_TEMPLATE/*.yml.
TEMPLATE_NOISE = [
    re.compile(p)
    for p in (
        r"### Is there an existing issue for this\?",
        r"- \[[xX ]\] I have searched the existing issues",
        r"### What happened\?",
        r"### Record",
        r"- \[[xX ]\] I agree to follow this project's Code of Conduct",
        r"- \[[xX ]\] I want to work on this issue",
        r"### Describe the feature",
        r"### Add ScreenShots",
        r"### What's wrong with the existing documentation",
        r"_No response_",
        r"<img[^>]*>",
        r"!\[[^\]]*\]\([^)]*\)",
        r"https?://\S+",
    )
]
# Only bracketed or colon-terminated prefixes, so "Bug in search" keeps its first word.
_PREFIX_WORD = r"(?:bug|feat|feature|docs?|enhancement)"
TITLE_PREFIX = re.compile(
    rf"^\s*(?:(?:\[{_PREFIX_WORD}\]|{_PREFIX_WORD}\s*:)\s*:?\s*)+", re.IGNORECASE
)


class Issue(TypedDict):
    number: int
    title: str
    body: str
    url: str
    state: str
    state_reason: str | None
    created_at: str
    labels: list[str]
    duplicate_of: int | None
    closed_by: list[int]


Transport = Callable[[str, dict, str], dict]


def post_graphql(query: str, variables: dict, token: str) -> dict:
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "pictopy-issue-triage",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def parse_issue(node: dict) -> Issue:
    reason = node.get("stateReason")
    duplicate_of = node.get("duplicateOf")
    closing_prs = node.get("closedByPullRequestsReferences") or {"nodes": []}
    return {
        "number": node["number"],
        "title": node["title"],
        "body": node.get("body") or "",
        "url": node["url"],
        "state": node["state"].lower(),
        "state_reason": reason.lower() if reason else None,
        "created_at": node["createdAt"],
        "labels": [label["name"] for label in node["labels"]["nodes"]],
        "duplicate_of": duplicate_of["number"] if duplicate_of else None,
        # Closed-but-unmerged pull requests also reference the issue; only merged
        # ones resolved it.
        "closed_by": [pr["number"] for pr in closing_prs["nodes"] if pr["merged"]],
    }


def fetch_issues(
    repository: str, token: str, transport: Transport = post_graphql
) -> list[Issue]:
    owner, name = repository.split("/", 1)
    issues: list[Issue] = []
    after: str | None = None
    while True:
        variables = {"owner": owner, "name": name, "after": after}
        connection = transport(ISSUES_QUERY, variables, token)["repository"]["issues"]
        issues.extend(parse_issue(node) for node in connection["nodes"])
        if not connection["pageInfo"]["hasNextPage"]:
            return issues
        after = connection["pageInfo"]["endCursor"]


def is_duplicate(issue: Issue) -> bool:
    # Before GitHub added the duplicate close reason (Oct 2025), maintainers closed
    # duplicates as completed and added a "duplicate" label instead.
    return (
        issue["state_reason"] == "duplicate"
        or issue["duplicate_of"] is not None
        or any(label.lower() == "duplicate" for label in issue["labels"])
    )


def status(issue: Issue) -> str:
    if issue["state"] == "open":
        return "open"
    if is_duplicate(issue):
        return "closed as duplicate"
    if issue["state_reason"] in ("completed", "not_planned"):
        return f"closed as {issue['state_reason'].replace('_', ' ')}"
    return "closed"


def resolve_canonical(
    number: int, by_number: dict[int, Issue], max_depth: int = MAX_DUPLICATE_DEPTH
) -> int:
    """Follow duplicate_of links to the issue that was kept, stopping on a cycle."""
    seen = {number}
    current = number
    for _ in range(max_depth):
        target = by_number[current]["duplicate_of"]
        if target is None or target not in by_number or target in seen:
            break
        seen.add(target)
        current = target
    return current


def clean_title(title: str) -> str:
    return TITLE_PREFIX.sub("", title).strip()


def clean_body(body: str) -> str:
    for pattern in TEMPLATE_NOISE:
        body = pattern.sub(" ", body)
    return re.sub(r"\s+", " ", body).strip()


def issue_text(issue: dict) -> str:
    return f"{clean_title(issue['title'])}. {clean_body(issue['body'] or '')}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", help="OWNER/REPO")
    parser.add_argument("out_json", type=Path)
    args = parser.parse_args()

    issues = fetch_issues(args.repository, os.environ["GITHUB_TOKEN"])
    args.out_json.write_text(json.dumps(issues), encoding="utf-8")
    print(f"Fetched {len(issues)} issues from {args.repository}")


if __name__ == "__main__":
    main()
