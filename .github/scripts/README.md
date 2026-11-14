# Issue triage scripts

`.github/workflows/issue-triage.yml` runs these when an issue is opened, or when its
title or body is edited:

1. `issue_corpus.py` fetches every issue through the GraphQL API, with its close reason,
   labels, the issue it duplicates, and the pull requests that closed it. It uses only
   the standard library, so it runs before any third-party package is installed.
2. `detect_duplicate_issue.py` compares the issue with every older issue, by cleaned
   title and by cleaned title plus body. An issue matches when its title similarity is at
   least `TITLE_THRESHOLD` or its title-plus-body similarity is at least
   `BODY_THRESHOLD`. A match on an issue closed as a duplicate is reported as the issue
   it duplicates, following chains such as #700 -> #693 -> #638.
3. `duplicate_comment.py` renders up to three matches, grouped by whether they are open,
   resolved, or closed as not planned, plus at most one tracking issue. The workflow keeps one comment per issue,
   updating it on edits and deleting it if nothing matches any more. Issues are
   referenced by number only, so no text from other issues is copied into the comment.

## Tracking issues

Maintainers often fold a narrow issue into a broader one, such as a logout button into
"Implement Settings UI". Their text differs too much for normal matching, so open issues
labelled `tracking` are matched with lower thresholds (`TRACKING_TITLE_THRESHOLD`,
`TRACKING_BODY_THRESHOLD`) and shown in their own section. Label an issue `tracking` when
it collects a whole area of work and narrower requests should be discussed there.
Labelling too many issues this way adds noise, so measure a proposed set first with
`--assume-tracking`, described below.

## Measuring a change to duplicate detection

Any change to the detector's text, model, threshold or ranking should be measured
before it ships. `eval_duplicate_detection.py` replays the detector over the
repository's real issues. Each issue is compared only with issues older than it, as it
would have been on the day it was opened.

```bash
pip install --only-binary :all: -r .github/scripts/requirements.txt
python .github/scripts/eval_duplicate_detection.py --json eval.json
```

The first run fetches every issue and caches it in `.github/scripts/.duplicate_eval_cache/`.
Pass `--refresh` to re-fetch. Set `GITHUB_TOKEN` to avoid the 60-requests-per-hour
unauthenticated limit.

### Dependencies and the model

`requirements.txt` is a hash-pinned lock generated from `requirements.in`; the command
to regenerate it is at the top of `requirements.in`. Embeddings come from fastembed's
ONNX export of `all-MiniLM-L6-v2`, pinned by `MODEL_REVISION` in
`detect_duplicate_issue.py`. It scores the same as the PyTorch model to four decimal
places, without installing torch. Changing the model or its revision changes every
score, so re-run the harness and retune the thresholds when you do.

The first line, **detector as shipped**, runs the detector's own `find_duplicates`, and
breaks duplicates shown down by pair `kind`. Pass `--assume-tracking 546,555` to treat
those issues as labelled `tracking` for the run. The
rest sweep each text the detector scores (`title`, `body`) and `raw`, the uncleaned text
it used before, across thresholds. The harness fetches through REST, which has no
duplicate links, so it does not redirect duplicates to the issue they duplicate.

The report shows, for each text variant and threshold:

- **flagged**: the share of issues opened since `--since` that would get a comment.
- **duplicates shown**: the share of labelled duplicate pairs where the bot would show
  the right issue.
- **hard negatives shown**: the share of labelled non-duplicates the bot would show.

Compare variants at the same flag rate, not the same threshold, because models and text
variants put scores on different scales.

### Feedback from real outcomes

`duplicate_feedback.py` checks the bot's comments against what maintainers and authors
did next. `.github/workflows/duplicate-detection-report.yml` runs it on the first of
each month, and on demand from the Actions tab, and writes the report to the run's
summary page. It reports how often the bot commented, how often a suggestion was
confirmed by a duplicate closure, and how often an author disputed one. It also lists
duplicates the bot missed and disputed suggestions, formatted as entries for
`duplicate_eval_pairs.json`, so the labelled pairs grow with every report.

To run it locally, set `GITHUB_TOKEN`; the GraphQL API needs one even for public data:

```bash
python .github/scripts/duplicate_feedback.py AOSSIE-Org/PictoPy --since 2026-09-01
```

### Labelled pairs

`duplicate_eval_pairs.json` holds the ground truth.

- **positives**: an issue and the older issue it duplicates. `source` is
  `github-duplicate` when a maintainer closed it as a duplicate, or `hand-judged`.
  `kind` is `same-report` when both describe the same problem, or `covered-by-umbrella`
  when a maintainer folded a narrower issue into a broader one. Text similarity rarely
  finds the second kind.
- **negatives**: pairs the bot has flagged that are not duplicates. `source` is
  `author-disputed` when the issue author explained why, or `hand-judged`.

Add a pair whenever a maintainer closes an issue as a duplicate, or an author disputes a
suggestion. Keep the candidate older than the issue.
