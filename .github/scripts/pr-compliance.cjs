const PASSED_LABEL = 'compliance:passed';
const FAILED_LABEL = 'compliance:failed';
// Label applied to issues that require screenshots/video in the PR (see issue #1534)
const VISUAL_PROOF_LABEL = 'requires:image-video-proof';
const COMMENT_MARKER = '<!-- pr-compliance -->';

const LABEL_DEFINITIONS = {
  [PASSED_LABEL]: {
    color: '0e8a16',
    description: 'PR meets the contribution requirements',
  },
  [FAILED_LABEL]: {
    color: 'd73a4a',
    description: 'PR does not yet meet the contribution requirements',
  },
};

// A PR counts as having visual proof only if it embeds or links to actual media.
// A bare filename such as "logo.png" in plain text does not qualify.
const VISUAL_PROOF_PATTERNS = [
  // Markdown image embed: ![alt](url)
  /!\[[^\]]*\]\([^)]+\)/,
  // HTML <img> / <video> tag with a src attribute
  /<(?:img|video)\b[^>]*\bsrc\s*=/i,
  // GitHub upload links (uploaded videos are pasted as bare URLs)
  /https?:\/\/github\.com\/user-attachments\/assets\/[\w-]+/i,
  // Direct link (bare or markdown link) to an image/video file
  /https?:\/\/[^\s)>"']+\.(?:png|jpe?g|gif|webp|mp4|mov|webm)(?:\?[^\s)>"']*)?(?=[\s)>"']|$)/i,
];

function hasVisualProof(body) {
  // Ignore HTML comments so template placeholders don't count as proof
  const visibleBody = body.replace(/<!--[\s\S]*?-->/g, '');
  return VISUAL_PROOF_PATTERNS.some((pattern) => pattern.test(visibleBody));
}

// Assignees are capped at 10 per issue by GitHub, so first: 20 can never truncate.
const LINKED_ISSUES_QUERY = `
  query ($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        closingIssuesReferences(first: 50, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            number
            assignees(first: 20) { nodes { login } }
            labels(first: 100) {
              pageInfo { hasNextPage endCursor }
              nodes { name }
            }
          }
        }
      }
    }
  }
`;

const ISSUE_LABELS_QUERY = `
  query ($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        labels(first: 100, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes { name }
        }
      }
    }
  }
`;

const LINKED_PULL_REQUESTS_QUERY = `
  query ($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        closedByPullRequestsReferences(first: 50, after: $cursor, includeClosedPrs: false) {
          pageInfo { hasNextPage endCursor }
          nodes {
            number
            repository { nameWithOwner }
          }
        }
      }
    }
  }
`;

// Fetches every closing issue (all pages) with its full assignee and label lists,
// so the check never passes on a truncated result.
async function fetchLinkedIssues(github, owner, repo, prNumber) {
  const issues = [];
  let cursor = null;
  let hasNextPage = true;

  while (hasNextPage) {
    const result = await github.graphql(LINKED_ISSUES_QUERY, {
      owner: owner,
      repo: repo,
      number: prNumber,
      cursor: cursor,
    });
    const connection = result.repository.pullRequest.closingIssuesReferences;

    for (const node of connection.nodes) {
      const labels = node.labels.nodes.map((label) => label.name);

      let labelPage = node.labels.pageInfo;
      while (labelPage.hasNextPage) {
        const more = await github.graphql(ISSUE_LABELS_QUERY, {
          owner: owner,
          repo: repo,
          number: node.number,
          cursor: labelPage.endCursor,
        });
        const moreLabels = more.repository.issue.labels;
        for (const label of moreLabels.nodes) {
          labels.push(label.name);
        }
        labelPage = moreLabels.pageInfo;
      }

      issues.push({
        number: node.number,
        assignees: node.assignees.nodes.map((assignee) => assignee.login),
        labels: labels,
      });
    }

    hasNextPage = connection.pageInfo.hasNextPage;
    cursor = connection.pageInfo.endCursor;
  }

  return issues;
}

// Open PRs in this repo that would close the given issue.
async function fetchLinkedPullRequestNumbers(github, owner, repo, issueNumber) {
  const numbers = [];
  let cursor = null;
  let hasNextPage = true;

  while (hasNextPage) {
    const result = await github.graphql(LINKED_PULL_REQUESTS_QUERY, {
      owner: owner,
      repo: repo,
      number: issueNumber,
      cursor: cursor,
    });
    const connection = result.repository.issue.closedByPullRequestsReferences;

    for (const node of connection.nodes) {
      if (node.repository.nameWithOwner.toLowerCase() === `${owner}/${repo}`.toLowerCase()) {
        numbers.push(node.number);
      }
    }

    hasNextPage = connection.pageInfo.hasNextPage;
    cursor = connection.pageInfo.endCursor;
  }

  return numbers;
}

async function ensureLabelExists(github, owner, repo, name) {
  try {
    await github.rest.issues.getLabel({ owner: owner, repo: repo, name: name });
  } catch (error) {
    if (error.status !== 404) {
      throw error;
    }
    try {
      await github.rest.issues.createLabel({
        owner: owner,
        repo: repo,
        name: name,
        color: LABEL_DEFINITIONS[name].color,
        description: LABEL_DEFINITIONS[name].description,
      });
    } catch (createError) {
      // 422 means another run created it first
      if (createError.status !== 422) {
        throw createError;
      }
    }
  }
}

async function updateLabels({ github, core, owner, repo, pr, labelToAdd, labelToRemove }) {
  // Label problems must never stop the report comment from being posted
  try {
    await ensureLabelExists(github, owner, repo, labelToAdd);

    const currentLabels = pr.labels.map((label) => label.name);
    if (!currentLabels.includes(labelToAdd)) {
      await github.rest.issues.addLabels({
        owner: owner,
        repo: repo,
        issue_number: pr.number,
        labels: [labelToAdd],
      });
    }

    if (currentLabels.includes(labelToRemove)) {
      try {
        await github.rest.issues.removeLabel({
          owner: owner,
          repo: repo,
          issue_number: pr.number,
          name: labelToRemove,
        });
      } catch (error) {
        if (error.status !== 404) {
          throw error;
        }
      }
    }
  } catch (error) {
    core.warning(`Could not update compliance labels on #${pr.number}: ${error.message}`);
  }
}

async function postReport({ github, owner, repo, prNumber, message }) {
  const comments = await github.paginate(github.rest.issues.listComments, {
    owner: owner,
    repo: repo,
    issue_number: prNumber,
    per_page: 100,
  });

  let existingComment = null;
  for (const comment of comments) {
    if (comment.user?.type === 'Bot' && comment.body?.includes(COMMENT_MARKER)) {
      existingComment = comment;
    }
  }

  if (existingComment) {
    await github.rest.issues.updateComment({
      owner: owner,
      repo: repo,
      comment_id: existingComment.id,
      body: message,
    });
  } else {
    await github.rest.issues.createComment({
      owner: owner,
      repo: repo,
      issue_number: prNumber,
      body: message,
    });
  }
}

async function checkPullRequest({ github, core, owner, repo, prNumber }) {
  // Always load the PR fresh: the event payload can be stale, and issue-triggered
  // runs have no PR payload at all.
  const { data: pr } = await github.rest.pulls.get({
    owner: owner,
    repo: repo,
    pull_number: prNumber,
  });

  if (pr.state !== 'open' || pr.user.type === 'Bot') {
    core.info(`Skipping #${prNumber} (closed or bot-authored).`);
    return;
  }

  const author = pr.user.login;
  const guidelines = `https://github.com/${owner}/${repo}/blob/HEAD/CONTRIBUTING.md`;
  const linkedIssues = await fetchLinkedIssues(github, owner, repo, pr.number);

  let authorIsAssigned = false;
  let needsVisualProof = false;
  const issueNumbers = [];
  for (const issue of linkedIssues) {
    issueNumbers.push(`#${issue.number}`);
    if (issue.assignees.includes(author)) {
      authorIsAssigned = true;
    }
    if (issue.labels.includes(VISUAL_PROOF_LABEL)) {
      needsVisualProof = true;
    }
  }
  const issueRefs = issueNumbers.join(', ');

  const visualProofPresent = hasVisualProof(pr.body || '');

  const problems = [];
  if (linkedIssues.length === 0) {
    problems.push(
      'No linked issue. Add a closing keyword to the PR description, e.g. `Fixes #123`.',
    );
  } else if (!authorIsAssigned) {
    problems.push(
      `@${author} is not assigned to the linked issue (${issueRefs}). Wait for a maintainer to assign you before opening a PR.`,
    );
  }
  if (needsVisualProof && !visualProofPresent) {
    problems.push(
      `The linked issue is labelled \`${VISUAL_PROOF_LABEL}\`. Add a screenshot or video of the change to the PR description, before and after if possible.`,
    );
  }

  let labelToAdd;
  let labelToRemove;
  let message = COMMENT_MARKER + '\n';
  if (problems.length === 0) {
    labelToAdd = PASSED_LABEL;
    labelToRemove = FAILED_LABEL;
    message += '### PR compliance check passed\n\n';
    message += `Linked issue: ${issueRefs}. Thanks for following the [contribution guidelines](${guidelines})!`;
  } else {
    labelToAdd = FAILED_LABEL;
    labelToRemove = PASSED_LABEL;
    message += '### PR compliance check failed\n\n';
    message += `This PR does not yet follow the [contribution guidelines](${guidelines}):\n\n`;
    for (const problem of problems) {
      message += `- ${problem}\n`;
    }
    message +=
      '\nThis check does not block merging, but please fix the above so maintainers can review your PR. It re-runs whenever you edit the PR, push a commit, or the linked issue\'s assignees or proof label change.';
  }
  core.info(message);

  await updateLabels({ github, core, owner, repo, pr, labelToAdd, labelToRemove });
  await postReport({ github, owner, repo, prNumber: pr.number, message });
}

module.exports = async ({ github, context, core }) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  let prNumbers;
  if (context.payload.pull_request) {
    prNumbers = [context.payload.pull_request.number];
  } else if (context.payload.issue) {
    // Issue assigned/unassigned/labeled: recheck every open PR that closes it
    prNumbers = await fetchLinkedPullRequestNumbers(github, owner, repo, context.payload.issue.number);
    core.info(`Issue #${context.payload.issue.number} is linked to PRs: ${prNumbers.join(', ') || 'none'}`);
  } else {
    core.info('Unsupported event, nothing to check.');
    return;
  }

  const failures = [];
  for (const prNumber of prNumbers) {
    try {
      await checkPullRequest({ github, core, owner, repo, prNumber });
    } catch (error) {
      failures.push(`#${prNumber}: ${error.message}`);
    }
  }
  if (failures.length > 0) {
    core.setFailed(`Compliance check failed to run for: ${failures.join('; ')}`);
  }
};
