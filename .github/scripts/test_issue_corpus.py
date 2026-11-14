"""Run with: python .github/scripts/test_issue_corpus.py"""

from issue_corpus import (
    clean_body,
    clean_title,
    fetch_issues,
    is_duplicate,
    parse_issue,
    resolve_canonical,
    status,
)


def make_issue(number: int, **fields) -> dict:
    issue = {
        "number": number,
        "title": f"Issue {number}",
        "body": "",
        "url": f"https://github.com/o/r/issues/{number}",
        "state": "closed",
        "state_reason": "completed",
        "created_at": "2026-01-01T00:00:00Z",
        "labels": [],
        "duplicate_of": None,
        "closed_by": [],
    }
    issue.update(fields)
    return issue


def make_node(number: int, **fields) -> dict:
    node = {
        "number": number,
        "title": f"Issue {number}",
        "body": "Body",
        "url": f"https://github.com/o/r/issues/{number}",
        "state": "OPEN",
        "stateReason": None,
        "createdAt": "2026-01-01T00:00:00Z",
        "labels": {"nodes": []},
        "duplicateOf": None,
        "closedByPullRequestsReferences": {"nodes": []},
    }
    node.update(fields)
    return node


def test_parse_issue_normalises_graphql_node() -> None:
    issue = parse_issue(
        make_node(
            700,
            state="CLOSED",
            stateReason="DUPLICATE",
            labels={"nodes": [{"name": "bug"}, {"name": "duplicate"}]},
            duplicateOf={"number": 693},
            closedByPullRequestsReferences={"nodes": [{"number": 701}]},
        )
    )
    assert issue["state"] == "closed"
    assert issue["state_reason"] == "duplicate"
    assert issue["labels"] == ["bug", "duplicate"]
    assert issue["duplicate_of"] == 693
    assert issue["closed_by"] == [701]

    open_issue = parse_issue(make_node(5, body=None))
    assert open_issue["state_reason"] is None
    assert open_issue["duplicate_of"] is None
    assert open_issue["body"] == ""


def test_fetch_issues_follows_cursor_until_last_page() -> None:
    pages = {
        None: ([make_node(1), make_node(2)], True, "c1"),
        "c1": ([make_node(3)], False, None),
    }
    calls = []

    def transport(query: str, variables: dict, token: str) -> dict:
        calls.append((variables, token))
        nodes, has_next, cursor = pages[variables["after"]]
        return {
            "repository": {
                "issues": {
                    "nodes": nodes,
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                }
            }
        }

    issues = fetch_issues("o/r", "tok", transport)
    assert [i["number"] for i in issues] == [1, 2, 3]
    assert [c[0]["after"] for c in calls] == [None, "c1"]
    assert calls[0] == ({"owner": "o", "name": "r", "after": None}, "tok")


def test_is_duplicate_covers_reason_link_and_legacy_label() -> None:
    assert is_duplicate(make_issue(1, state_reason="duplicate"))
    assert is_duplicate(make_issue(2, duplicate_of=1))
    assert is_duplicate(make_issue(3, labels=["Duplicate"]))
    assert not is_duplicate(make_issue(4))


def test_status_names_closure_reason() -> None:
    assert status(make_issue(1, state="open", state_reason="reopened")) == "open"
    assert status(make_issue(2)) == "closed as completed"
    assert status(make_issue(3, state_reason="not_planned")) == "closed as not planned"
    assert status(make_issue(4, labels=["duplicate"])) == "closed as duplicate"
    assert status(make_issue(5, state_reason=None)) == "closed"


def test_resolve_canonical_follows_chain() -> None:
    by_number = {
        638: make_issue(638),
        693: make_issue(693, duplicate_of=638),
        700: make_issue(700, duplicate_of=693),
    }
    assert resolve_canonical(700, by_number) == 638
    assert resolve_canonical(638, by_number) == 638


def test_resolve_canonical_stops_on_cycle_missing_target_and_depth() -> None:
    cycle = {1: make_issue(1, duplicate_of=2), 2: make_issue(2, duplicate_of=1)}
    assert resolve_canonical(1, cycle) == 2

    missing = {3: make_issue(3, duplicate_of=99)}
    assert resolve_canonical(3, missing) == 3

    chain = {
        n: make_issue(n, duplicate_of=n - 1 if n > 1 else None) for n in range(1, 9)
    }
    assert resolve_canonical(8, chain, max_depth=5) == 3


def test_clean_title_strips_template_prefixes() -> None:
    assert clean_title("BUG: Search is slow") == "Search is slow"
    assert clean_title("[Bug]: Search is slow") == "Search is slow"
    assert clean_title("Feat:Albums page") == "Albums page"
    assert clean_title("BUG:BUG: Inefficient loop") == "Inefficient loop"
    assert clean_title("Bugfix for albums") == "Bugfix for albums"
    assert clean_title("Bug in search") == "Bug in search"


def test_clean_body_strips_issue_template_scaffolding() -> None:
    body = (
        "### Is there an existing issue for this?\n\n"
        "- [X] I have searched the existing issues\n\n"
        "### What happened?\n\nThe gallery freezes.\n\n"
        "### Record\n\n- [x] I agree to follow this project's Code of Conduct\n"
        "_No response_ ![shot](https://example.com/a.png)"
    )
    assert clean_body(body) == "The gallery freezes."


if __name__ == "__main__":
    test_parse_issue_normalises_graphql_node()
    test_fetch_issues_follows_cursor_until_last_page()
    test_is_duplicate_covers_reason_link_and_legacy_label()
    test_status_names_closure_reason()
    test_resolve_canonical_follows_chain()
    test_resolve_canonical_stops_on_cycle_missing_target_and_depth()
    test_clean_title_strips_template_prefixes()
    test_clean_body_strips_issue_template_scaffolding()
    print("All tests passed.")
