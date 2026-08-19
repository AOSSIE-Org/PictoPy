import os

import pytest
from platformdirs import user_data_dir

from app.config.settings import DATABASE_PATH
from app.database.connection import DATABASE_PATH as CONNECTION_DATABASE_PATH
from tests import db_isolation


def test_test_mode_redirects_database_path() -> None:
    assert os.environ["TEST_MODE"] == "true"
    assert os.path.basename(DATABASE_PATH) == "test_db.sqlite3"


def test_database_path_is_outside_the_user_library() -> None:
    library_dir = os.path.abspath(user_data_dir("PictoPy"))
    resolved = os.path.abspath(DATABASE_PATH)
    assert os.path.commonpath([resolved, library_dir]) != library_dir


def test_connection_module_uses_the_redirected_path() -> None:
    # The connection module binds DATABASE_PATH at import time, so a redirect that
    # lands after it would leave every query pointed at the real library.
    assert CONNECTION_DATABASE_PATH == DATABASE_PATH


def test_guard_rejects_a_path_inside_the_user_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library_db = os.path.join(user_data_dir("PictoPy"), "database", "PictoPy.db")
    monkeypatch.setattr(db_isolation, "DATABASE_PATH", library_db)

    with pytest.raises(RuntimeError, match="Refusing to run tests"):
        db_isolation._assert_not_user_library()
