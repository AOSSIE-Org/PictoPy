const PASSED_LABEL = 'compliance:passed';
const FAILED_LABEL = 'compliance:failed';
const VISUAL_PROOF_LABEL = 'frontend';
const COMMENT_MARKER = '<!-- pr-compliance -->';

// Images, videos, or GitHub upload links (uploaded videos are bare URLs) in pattern regex
const VISUAL_PROOF_PATTERN =
  /!\[[^\]]*\]\([^)]+\)|<(img|video)\s|github\.com\/user-attachments\/assets\/|\.(png|jpe?g|gif|webp|mp4|mov|webm)\b/i;

const LINKED_ISSUES_QUERY = `
  query ($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        closingIssuesReferences(first: 10) {
          nodes {
            number
            assignees(first: 20) { nodes { login } }
            labels(first: 50) { nodes { name } }
          }
        }
      }
    }
  }
`;

module.exports = async ({ github, context, core }) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const pr = context.payload.pull_request;
  const author = pr.user.login;
  const prBody = pr.body || '';
  const guidelines = `https://github.com/${owner}/${repo}/blob/HEAD/CONTRIBUTING.md`;

  const result = await github.graphql(LINKED_ISSUES_QUERY, {
    owner: owner,
    repo: repo,
    number: pr.number,
  });
  const linkedIssues = result.repository.pullRequest.closingIssuesReferences.nodes;

  let authorIsAssigned = false;
  let needsVisualProof = false;
  const issueNumbers = [];
  for (const issue of linkedIssues) {
    issueNumbers.push(`#${issue.number}`);

    for (const assignee of issue.assignees.nodes) {
      if (assignee.login === author) {
        authorIsAssigned = true;
      }
    }

    for (const label of issue.labels.nodes) {
      if (label.name === VISUAL_PROOF_LABEL) {
        needsVisualProof = true;
      }
    }
  }
  const issueRefs = issueNumbers.join(', ');

  const hasVisualProof = VISUAL_PROOF_PATTERN.test(prBody);

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
  if (needsVisualProof && !hasVisualProof) {
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
    message += '###  PR compliance check failed\n\n';
    message += `This PR does not yet follow the [contribution guidelines](${guidelines}):\n\n`;
    for (const problem of problems) {
      message += `- ${problem}\n`;
    }
    message +=
      '\nThis check does not block merging, but please fix the above so maintainers can review your PR. It re runs whenever you edit the PR or push a commit.';
  }
  core.info(message);

  await github.rest.issues.addLabels({
    owner: owner,
    repo: repo,
    issue_number: pr.number,
    labels: [labelToAdd],
  });

  for (const label of pr.labels) {
    if (label.name === labelToRemove) {
      await github.rest.issues.removeLabel({
        owner: owner,
        repo: repo,
        issue_number: pr.number,
        name: labelToRemove,
      });
    }
  }

  const comments = await github.paginate(github.rest.issues.listComments, {
    owner: owner,
    repo: repo,
    issue_number: pr.number,
    per_page: 100,
  });

  let existingComment = null;
  for (const comment of comments) {
    if (comment.user.type === 'Bot' && comment.body.includes(COMMENT_MARKER)) {
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
      issue_number: pr.number,
      body: message,
    });
  }
};
