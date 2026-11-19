from watchfiles import Change

from app.utils.watcher_helpers import format_debug_changes


def test_empty_changes_return_empty_string():
    assert format_debug_changes(set()) == ""


def test_each_change_type_is_labelled():
    changes = {
        (Change.added, "/a/new.jpg"),
        (Change.modified, "/a/edit.jpg"),
        (Change.deleted, "/a/gone.jpg"),
    }

    lines = [line.strip() for line in format_debug_changes(changes).splitlines()]

    assert lines == [
        "- modified: /a/edit.jpg",
        "- deleted: /a/gone.jpg",
        "- added: /a/new.jpg",
    ]


def test_output_is_sorted_by_path_and_indented():
    changes = {(Change.added, "/b.jpg"), (Change.added, "/a.jpg")}

    result = format_debug_changes(changes)

    assert result.splitlines()[0].endswith("/a.jpg")
    assert result.splitlines()[1].endswith("/b.jpg")
    assert all(line.startswith("      - ") for line in result.splitlines())


def test_none_path_does_not_raise():
    result = format_debug_changes({(Change.added, None), (Change.added, "/a.jpg")})

    assert "Error formatting changes" not in result
    assert "/a.jpg" in result
