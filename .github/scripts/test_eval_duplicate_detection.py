"""Run with: python .github/scripts/test_eval_duplicate_detection.py"""

from eval_duplicate_detection import (
    clean_body,
    clean_title,
    load_pairs,
    next_link,
    percentile,
    rank_of,
    summarise,
    top_matches,
)


def test_next_link_follows_cursor_and_stops_on_last_page() -> None:
    header = (
        '<https://api.github.com/repositories/1/issues?after=abc>; rel="next", '
        '<https://api.github.com/repositories/1/issues?before=xyz>; rel="prev"'
    )
    assert next_link(header) == "https://api.github.com/repositories/1/issues?after=abc"
    assert next_link('<https://x/issues?before=xyz>; rel="prev"') is None
    assert next_link("") is None


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


def test_percentile_interpolates_like_numpy() -> None:
    values = [0.1, 0.4, 0.2, 0.3]
    assert percentile(values, 0) == 0.1
    assert percentile(values, 100) == 0.4
    assert abs(percentile(values, 50) - 0.25) < 1e-9
    assert abs(percentile(values, 90) - 0.37) < 1e-9


def test_rank_of_counts_strictly_higher_scores() -> None:
    assert rank_of([0.2, 0.9, 0.5], 1) == 1
    assert rank_of([0.2, 0.9, 0.5], 0) == 3
    assert rank_of([0.5, 0.5, 0.1], 1) == 1


def test_top_matches_applies_every_gate_and_ranks_by_rank_scores() -> None:
    body = [0.9, 0.8, 0.7, 0.6]
    title = [0.1, 0.9, 0.9, 0.9]
    assert top_matches(body, [(body, 0.65)]) == [0, 1, 2]
    assert top_matches(body, [(body, 0.65)], max_results=2) == [0, 1]
    assert top_matches(body, [(title, 0.5), (body, 0.65)]) == [1, 2]
    assert top_matches(body, [(body, 0.95)]) == []


def test_summarise_counts_flags_and_shown_pairs() -> None:
    shown = {10: [3], 11: [], 12: [5, 4]}
    positives = [
        {"issue": 10, "candidate": 3, "source": "s"},
        {"issue": 12, "candidate": 1, "source": "s"},
    ]
    negatives = [{"issue": 12, "candidate": 4, "source": "s"}]
    outcome = summarise(shown, [10, 11, 12], positives, negatives)
    assert abs(outcome["flag_rate"] - 2 / 3) < 1e-9
    assert outcome["positives_shown"] == 0.5
    assert outcome["negatives_shown"] == 1.0


def test_labelled_pairs_are_well_formed() -> None:
    _, positives, negatives = load_pairs()
    keys = [(p["issue"], p["candidate"]) for p in positives + negatives]
    assert len(keys) == len(set(keys)), "a pair is listed twice"
    for issue, candidate in keys:
        assert candidate < issue, f"#{issue} -> #{candidate}: candidate must be older"
    assert {p["kind"] for p in positives} <= {"same-report", "covered-by-umbrella"}


if __name__ == "__main__":
    test_next_link_follows_cursor_and_stops_on_last_page()
    test_clean_title_strips_template_prefixes()
    test_clean_body_strips_issue_template_scaffolding()
    test_percentile_interpolates_like_numpy()
    test_rank_of_counts_strictly_higher_scores()
    test_top_matches_applies_every_gate_and_ranks_by_rank_scores()
    test_summarise_counts_flags_and_shown_pairs()
    test_labelled_pairs_are_well_formed()
    print("All tests passed.")
