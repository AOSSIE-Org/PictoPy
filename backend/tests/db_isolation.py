"""Points the database at a throwaway file before anything imports app.config."""

import os

# settings.py resolves DATABASE_PATH at import time, so this has to happen before
# any app import. CI gets the same redirect for free via GITHUB_ACTIONS.
os.environ["TEST_MODE"] = "true"

from app.config.settings import DATABASE_PATH  # noqa: E402
from platformdirs import user_data_dir  # noqa: E402


def _assert_not_user_library() -> None:
    # The suite drops and truncates tables, so a silent redirect failure would
    # destroy a real library. Fail the session instead.
    library_dir = os.path.abspath(user_data_dir("PictoPy"))
    resolved = os.path.abspath(DATABASE_PATH)
    if os.path.commonpath([resolved, library_dir]) == library_dir:
        raise RuntimeError(
            f"Refusing to run tests against the PictoPy library database: {resolved}"
        )


_assert_not_user_library()
