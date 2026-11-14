"""Run from .github/scripts/duplicate_detection with: python -m tests.test_detect_duplicate_issue"""

from detect_duplicate_issue import candidates, dot_product, find_duplicates, title_text
from tests.test_issue_corpus import make_issue


def test_dot_product_matches_cosine_similarity_for_normalized_vectors() -> None:
    assert dot_product([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert dot_product([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_title_text_is_the_cleaned_title() -> None:
    issue = make_issue(1, title="BUG: Gallery freezes", body="Long body text")
    assert title_text(issue) == "Gallery freezes"


def test_find_duplicates_filters_below_threshold_and_sorts_descending() -> None:
    others = [
        make_issue(1, state="open", state_reason=None),
        make_issue(2, state="open", state_reason=None),
        make_issue(3, closed_by=[30]),
    ]

    matches = find_duplicates([0.3, 0.9, 0.75], [0.0] * 3, others)

    assert [m["number"] for m in matches] == [2, 3]
    assert matches[0]["status"] == "open"
    assert matches[1]["status"] == "closed as completed"
    assert matches[1]["closed_by"] == [30]
    assert matches[0]["also_reported_as"] == []


def test_find_duplicates_accepts_a_close_body_match_with_a_different_title() -> None:
    others = [make_issue(1), make_issue(2), make_issue(3)]
    title_scores = [0.2, 0.75, 0.65]
    body_scores = [0.85, 0.3, 0.79]

    matches = find_duplicates(title_scores, body_scores, others)

    # Issue 3 passes neither threshold; issues 1 and 2 rank by their better score.
    assert [m["number"] for m in matches] == [1, 2]
    assert matches[0]["score"] == 0.85


def test_find_duplicates_respects_max_results() -> None:
    others = [make_issue(i) for i in range(5)]

    matches = find_duplicates([0.9] * 5, [0.0] * 5, others, max_results=3)

    assert len(matches) == 3


def test_find_duplicates_reports_canonical_issue_for_duplicate_matches() -> None:
    others = [
        make_issue(638, title="Onboarding issues"),
        make_issue(693, state_reason="duplicate", duplicate_of=638),
        make_issue(700, state_reason="duplicate", duplicate_of=693),
        make_issue(800, title="Other"),
    ]
    # The canonical #638 scores below threshold on its own; its duplicates do not.
    scores = [0.4, 0.8, 0.9, 0.75]

    matches = find_duplicates(scores, [0.0] * 4, others)

    assert [m["number"] for m in matches] == [638, 800]
    assert matches[0]["title"] == "Onboarding issues"
    assert matches[0]["score"] == 0.9
    assert matches[0]["also_reported_as"] == [693, 700]


def test_find_duplicates_keeps_duplicate_without_known_target() -> None:
    others = [make_issue(66, labels=["duplicate"])]

    matches = find_duplicates([0.9], [0.0], others)

    assert [m["number"] for m in matches] == [66]
    assert matches[0]["status"] == "closed as duplicate"


def test_candidates_are_issues_opened_before_the_current_one() -> None:
    corpus = [
        make_issue(5, created_at="2026-01-01T00:00:00Z"),
        make_issue(9, created_at="2026-03-01T00:00:00Z"),
        make_issue(12, created_at="2026-05-01T00:00:00Z"),
    ]
    current = {"number": 9, "created_at": "2026-03-01T00:00:00Z"}
    assert [i["number"] for i in candidates(corpus, current)] == [5]


def test_find_duplicates_uses_lower_bar_for_tracking_issues() -> None:
    others = [
        make_issue(1, state="open", state_reason=None, labels=["tracking"]),
        make_issue(2, state="open", state_reason=None, labels=["tracking"]),
        make_issue(3, labels=["tracking"]),
        make_issue(4),
        make_issue(5),
        make_issue(6),
    ]
    title_scores = [0.55, 0.52, 0.55, 0.9, 0.8, 0.75]

    matches = find_duplicates(title_scores, [0.0] * 6, others)

    # One tracking match at most, on top of the usual three; a closed issue with
    # the label is held to the normal bar.
    assert [m["number"] for m in matches] == [1, 4, 5, 6]
    assert matches[0]["status"] == "tracking"


if __name__ == "__main__":
    test_dot_product_matches_cosine_similarity_for_normalized_vectors()
    test_title_text_is_the_cleaned_title()
    test_find_duplicates_accepts_a_close_body_match_with_a_different_title()
    test_find_duplicates_filters_below_threshold_and_sorts_descending()
    test_find_duplicates_respects_max_results()
    test_find_duplicates_reports_canonical_issue_for_duplicate_matches()
    test_find_duplicates_keeps_duplicate_without_known_target()
    test_candidates_are_issues_opened_before_the_current_one()
    test_find_duplicates_uses_lower_bar_for_tracking_issues()
    print("All tests passed.")
