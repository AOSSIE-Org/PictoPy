# Issue triage scripts

`detect_duplicate_issue.py` is called by `.github/workflows/issue-triage.yml` when an
issue is opened. It suggests up to three similar existing issues.

## Measuring a change to duplicate detection

Any change to the detector's text, model, threshold or ranking should be measured
before it ships. `eval_duplicate_detection.py` replays the detector over the
repository's real issues. Each issue is compared only with issues older than it, as it
would have been on the day it was opened.

```bash
pip install sentence-transformers
python .github/scripts/eval_duplicate_detection.py --json eval.json
```

The first run fetches every issue and caches it in `.github/scripts/.duplicate_eval_cache/`.
Pass `--refresh` to re-fetch. Set `GITHUB_TOKEN` to avoid the 60-requests-per-hour
unauthenticated limit.

The report shows, for each text variant and threshold:

- **flagged**: the share of issues opened since `--since` that would get a comment.
- **duplicates shown**: the share of labelled duplicate pairs where the bot would show
  the right issue.
- **hard negatives shown**: the share of labelled non-duplicates the bot would show.

Compare variants at the same flag rate, not the same threshold, because models and text
variants put scores on different scales.

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
