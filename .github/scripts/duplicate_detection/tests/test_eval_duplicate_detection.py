"""Run from .github/scripts/duplicate_detection with: python -m tests.test_eval_duplicate_detection"""

from tests.test_issue_corpus import make_issue

from eval_duplicate_detection import (
    Pair,
    load_pairs,
    next_link,
    percentile,
    prefix_resolver,
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


def test_percentile_interpolates_like_numpy() -> None:
    values = [0.1, 0.4, 0.2, 0.3]
    assert percentile(values, 0) == 0.1
    assert percentile(values, 100) == 0.4
    assert abs((percentile(values, 50) or 0) - 0.25) < 1e-9
    assert abs((percentile(values, 90) or 0) - 0.37) < 1e-9
    assert percentile([], 50) is None


def test_rank_of_breaks_ties_like_top_matches() -> None:
    assert rank_of([0.2, 0.9, 0.5], 1) == 1
    assert rank_of([0.2, 0.9, 0.5], 0) == 3
    scores = [0.9, 0.9, 0.1]
    assert top_matches(scores, [(scores, 0.0)], max_results=1) == [0]
    assert rank_of(scores, 0) == 1
    assert rank_of(scores, 1) == 2


def test_top_matches_applies_every_gate_and_ranks_by_rank_scores() -> None:
    body = [0.9, 0.8, 0.7, 0.6]
    title = [0.1, 0.9, 0.9, 0.9]
    assert top_matches(body, [(body, 0.65)]) == [0, 1, 2]
    assert top_matches(body, [(body, 0.65)], max_results=2) == [0, 1]
    assert top_matches(body, [(title, 0.5), (body, 0.65)]) == [1, 2]
    assert top_matches(body, [(body, 0.95)]) == []


def test_summarise_counts_flags_and_shown_pairs() -> None:
    shown = {10: [3], 11: [], 12: [5, 4]}
    positives: list[Pair] = [
        {"issue": 10, "candidate": 3, "source": "s"},
        {"issue": 12, "candidate": 1, "source": "s"},
    ]
    negatives: list[Pair] = [{"issue": 12, "candidate": 4, "source": "s"}]
    outcome = summarise(shown, [10, 11, 12], positives, negatives)
    assert abs((outcome["flag_rate"] or 0) - 2 / 3) < 1e-9
    assert outcome["positives_shown"] == 0.5
    assert outcome["negatives_shown"] == 1.0
    assert summarise(shown, [10], [], [])["negatives_shown"] is None


def test_summarise_resolves_labelled_candidates_like_the_detector() -> None:
    # #1 was closed as a duplicate of #0, so the detector shows #0 for a match on #1.
    shown = {20: [0]}
    positives: list[Pair] = [{"issue": 20, "candidate": 1, "source": "s"}]
    assert summarise(shown, [20], positives, [])["positives_shown"] == 0.0
    canonical = {1: 0}.get
    outcome = summarise(shown, [20], positives, [], lambda q, n: canonical(n, n))
    assert outcome["positives_shown"] == 1.0


def test_prefix_resolver_only_follows_links_to_older_issues() -> None:
    corpus = [
        make_issue(1, duplicate_of=30),
        make_issue(5, duplicate_of=2),
        make_issue(2),
        make_issue(20),
        make_issue(30),
    ]
    canonical = prefix_resolver(corpus)
    # Query #20 cannot see #30, so the detector shows #1 itself.
    assert canonical(20, 1) == 1
    assert canonical(20, 5) == 2


def test_labelled_pairs_are_well_formed() -> None:
    _, positives, negatives = load_pairs()
    keys = [(p["issue"], p["candidate"]) for p in positives + negatives]
    assert len(keys) == len(set(keys)), "a pair is listed twice"
    for issue, candidate in keys:
        assert candidate < issue, f"#{issue} -> #{candidate}: candidate must be older"
    assert {p["kind"] for p in positives} <= {"same-report", "covered-by-umbrella"}


if __name__ == "__main__":
    test_next_link_follows_cursor_and_stops_on_last_page()
    test_percentile_interpolates_like_numpy()
    test_rank_of_breaks_ties_like_top_matches()
    test_top_matches_applies_every_gate_and_ranks_by_rank_scores()
    test_summarise_counts_flags_and_shown_pairs()
    test_summarise_resolves_labelled_candidates_like_the_detector()
    test_prefix_resolver_only_follows_links_to_older_issues()
    test_labelled_pairs_are_well_formed()
    print("All tests passed.")
