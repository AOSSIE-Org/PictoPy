from typing import Set, Tuple
from watchfiles import Change


def format_debug_changes(changes: Set[Tuple[Change, str]]) -> str:
    """
    Format file changes into a readable format.

    Args:
        changes: Set of (change_type, file_path) tuples from watchfiles

    Returns:
        Formatted string of change messages
    """
    if not changes:
        return ""
    debug_changes = []
    try:
        for change, path in sorted(
            changes, key=lambda x: x[1] if x[1] is not None else ""
        ):
            change_type = (
                "deleted"
                if change == Change.deleted
                else "modified" if change == Change.modified else "added"
            )
            debug_changes.append(f"  - {change_type}: {path}")
        indented = "\n".join("    " + line for line in debug_changes)
        return indented
    except Exception as e:
        return f"Error formatting changes: {str(e)}"
