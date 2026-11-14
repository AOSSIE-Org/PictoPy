"""Run with: python .github/scripts/test_duplicate_comment.py"""

from duplicate_comment import MARKER, render_comment


def make_match(number: int, status: str, **fields) -> dict:
    match = {
        "number": number,
        "title": "@someone [click](https://example.com)",
        "status": status,
        "closed_by": [],
        "also_reported_as": [],
        "score": 0.8,
    }
    match.update(fields)
    return match


def test_render_comment_returns_none_without_matches() -> None:
    assert render_comment([]) is None


def test_render_comment_groups_by_lifecycle_in_fixed_order() -> None:
    body = render_comment(
        [
            make_match(640, "closed as not planned"),
            make_match(1496, "open"),
            make_match(722, "closed as completed", closed_by=[730]),
        ]
    )
    assert body is not None
    assert body.startswith(MARKER)
    open_at = body.index("**Open**")
    resolved_at = body.index("**Previously resolved**")
    declined_at = body.index("**Closed as not planned**")
    assert open_at < resolved_at < declined_at
    assert "- #1496\n" in body
    assert "- #722 (fixed by #730)" in body
    assert "may be a regression" in body
    assert "- #640\n" in body


def test_render_comment_puts_tracking_issues_first() -> None:
    body = render_comment([make_match(1496, "open"), make_match(566, "tracking")])
    assert body is not None
    assert body.index("**Tracked in**") < body.index("**Open**")
    assert "- #566\n" in body


def test_render_comment_notes_duplicates_and_merges_closed_groups() -> None:
    body = render_comment(
        [
            make_match(638, "closed as duplicate", also_reported_as=[693, 700]),
            make_match(66, "closed"),
        ]
    )
    assert body is not None
    assert "- #638 (also reported as #693, #700)" in body
    assert body.count("**Other closed issues**") == 1
    assert "- #66" in body


def test_render_comment_never_echoes_other_issue_text_or_scores() -> None:
    body = render_comment([make_match(1, "open")])
    assert body is not None
    assert "@someone" not in body
    assert "example.com" not in body
    assert "%" not in body and "0.8" not in body


if __name__ == "__main__":
    test_render_comment_returns_none_without_matches()
    test_render_comment_groups_by_lifecycle_in_fixed_order()
    test_render_comment_puts_tracking_issues_first()
    test_render_comment_notes_duplicates_and_merges_closed_groups()
    test_render_comment_never_echoes_other_issue_text_or_scores()
    print("All tests passed.")
