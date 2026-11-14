"""Render the duplicate-detection comment from the detector's matches."""

from __future__ import annotations

# Lets the workflow find and update its own comment instead of posting another.
MARKER = "<!-- pictopy-duplicate-detection -->"

# (status, heading, advice) in display order. Statuses come from issue_corpus.status.
SECTIONS = (
    (
        "open",
        "Open",
        "If one of these describes the same problem, consider adding your details "
        "there instead.",
    ),
    (
        "closed as completed",
        "Previously resolved",
        "If you are seeing one of these again, please mention the version you are "
        "using, as it may be a regression.",
    ),
    (
        "closed as not planned",
        "Closed as not planned",
        "These were closed without being worked on. The discussion there may explain "
        "why.",
    ),
    ("closed as duplicate", "Other closed issues", ""),
    ("closed", "Other closed issues", ""),
)


def _item(match: dict, repository: str) -> str:
    # Issues are referenced by number only. GitHub renders the title itself, so text
    # from other issues is never echoed into the comment.
    def ref(number: int) -> str:
        return f"{repository}#{number}"

    notes = []
    if match["status"] == "closed as completed" and match["closed_by"]:
        notes.append("fixed by " + ", ".join(ref(n) for n in match["closed_by"]))
    if match["also_reported_as"]:
        reported = ", ".join(ref(n) for n in match["also_reported_as"])
        notes.append(f"also reported as {reported}")
    suffix = f" ({'; '.join(notes)})" if notes else ""
    return f"- {ref(match['number'])}{suffix}"


def render_comment(matches: list[dict], repository: str = "") -> str | None:
    """repository is "OWNER/REPO" when the matches live in a different repository."""
    if not matches:
        return None
    lines = [
        MARKER,
        "**Possibly related issues**",
        "",
        "These existing issues look similar. This is an automated suggestion: "
        "if none of them apply, no action is needed.",
    ]
    rendered: set[str] = set()
    for status, heading, advice in SECTIONS:
        group = [m for m in matches if m["status"] == status]
        if not group:
            continue
        if heading not in rendered:
            lines += ["", f"**{heading}**", ""]
            rendered.add(heading)
        lines += [_item(m, repository) for m in group]
        if advice:
            lines += ["", advice]
    return "\n".join(lines) + "\n"
