"""Run with: python .github/scripts/test_detect_duplicate_issue.py"""

from detect_duplicate_issue import dot_product, find_duplicates


def test_dot_product_matches_cosine_similarity_for_normalized_vectors() -> None:
    assert dot_product([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert dot_product([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_find_duplicates_filters_below_threshold_and_sorts_descending() -> None:
    others = [
        {"number": 1, "title": "unrelated", "url": "u1", "state": "open"},
        {"number": 2, "title": "near duplicate", "url": "u2", "state": "open"},
        {"number": 3, "title": "borderline duplicate", "url": "u3", "state": "closed"},
    ]
    current_embedding = [1.0, 0.0]
    other_embeddings = [[0.3, 0.0], [0.9, 0.0], [0.6, 0.0]]

    matches = find_duplicates(
        current_embedding, other_embeddings, others, threshold=0.55
    )

    assert [m["number"] for m in matches] == [2, 3]
    assert matches[0]["score"] == 90.0


def test_find_duplicates_respects_max_results() -> None:
    others = [
        {"number": i, "title": "t", "url": "u", "state": "open"} for i in range(5)
    ]
    current_embedding = [1.0]
    other_embeddings = [[0.9] for _ in others]

    matches = find_duplicates(
        current_embedding, other_embeddings, others, threshold=0.5, max_results=3
    )

    assert len(matches) == 3


if __name__ == "__main__":
    test_dot_product_matches_cosine_similarity_for_normalized_vectors()
    test_find_duplicates_filters_below_threshold_and_sorts_descending()
    test_find_duplicates_respects_max_results()
    print("All tests passed.")
