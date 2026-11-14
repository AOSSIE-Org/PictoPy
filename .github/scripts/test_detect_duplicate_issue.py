"""Run with: python .github/scripts/test_detect_duplicate_issue.py"""

from detect_duplicate_issue import dot_product, find_duplicates
from test_issue_corpus import make_issue


def test_dot_product_matches_cosine_similarity_for_normalized_vectors() -> None:
    assert dot_product([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert dot_product([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_find_duplicates_filters_below_threshold_and_sorts_descending() -> None:
    others = [
        make_issue(1, title="unrelated", state="open", state_reason=None),
        make_issue(2, title="near duplicate", state="open", state_reason=None),
        make_issue(3, title="borderline duplicate"),
    ]
    current_embedding = [1.0, 0.0]
    other_embeddings = [[0.3, 0.0], [0.9, 0.0], [0.6, 0.0]]

    matches = find_duplicates(
        current_embedding, other_embeddings, others, threshold=0.55
    )

    assert [m["number"] for m in matches] == [2, 3]
    assert matches[0]["score"] == 90.0
    assert matches[0]["status"] == "open"
    assert matches[1]["status"] == "closed as completed"
    assert matches[0]["also_reported_as"] == []


def test_find_duplicates_ranks_by_raw_score_not_rounded_display_value() -> None:
    others = [make_issue(1), make_issue(2), make_issue(3)]
    current_embedding = [1.0]
    # Issues 1 and 2 both round to 90.0; issue 2's raw score is higher.
    other_embeddings = [[0.9001], [0.9004], [0.95]]

    matches = find_duplicates(
        current_embedding, other_embeddings, others, threshold=0.5, max_results=2
    )

    assert [m["number"] for m in matches] == [3, 2]
    assert matches[1]["score"] == 90.0


def test_find_duplicates_respects_max_results() -> None:
    others = [make_issue(i) for i in range(5)]
    current_embedding = [1.0]
    other_embeddings = [[0.9] for _ in others]

    matches = find_duplicates(
        current_embedding, other_embeddings, others, threshold=0.5, max_results=3
    )

    assert len(matches) == 3


def test_find_duplicates_reports_canonical_issue_for_duplicate_matches() -> None:
    others = [
        make_issue(638, title="Onboarding issues"),
        make_issue(693, state_reason="duplicate", duplicate_of=638),
        make_issue(700, state_reason="duplicate", duplicate_of=693),
        make_issue(800, title="Other"),
    ]
    current_embedding = [1.0]
    # The canonical #638 scores below threshold on its own; its duplicates do not.
    other_embeddings = [[0.4], [0.7], [0.8], [0.6]]

    matches = find_duplicates(
        current_embedding, other_embeddings, others, threshold=0.55
    )

    assert [m["number"] for m in matches] == [638, 800]
    assert matches[0]["title"] == "Onboarding issues"
    assert matches[0]["score"] == 80.0
    assert matches[0]["also_reported_as"] == [693, 700]


def test_find_duplicates_keeps_duplicate_without_known_target() -> None:
    others = [make_issue(66, labels=["duplicate"])]

    matches = find_duplicates([1.0], [[0.9]], others, threshold=0.55)

    assert [m["number"] for m in matches] == [66]
    assert matches[0]["status"] == "closed as duplicate"


if __name__ == "__main__":
    test_dot_product_matches_cosine_similarity_for_normalized_vectors()
    test_find_duplicates_filters_below_threshold_and_sorts_descending()
    test_find_duplicates_ranks_by_raw_score_not_rounded_display_value()
    test_find_duplicates_respects_max_results()
    test_find_duplicates_reports_canonical_issue_for_duplicate_matches()
    test_find_duplicates_keeps_duplicate_without_known_target()
    print("All tests passed.")
