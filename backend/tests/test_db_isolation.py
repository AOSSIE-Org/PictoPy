import os
from pathlib import Path

import pytest
from platformdirs import user_data_dir

from app.config.settings import DATABASE_PATH
from app.database.connection import DATABASE_PATH as CONNECTION_DATABASE_PATH
from tests import db_isolation


def test_test_mode_redirects_database_path() -> None:
    assert os.environ["TEST_MODE"] == "true"
    assert os.path.basename(DATABASE_PATH) == "test_db.sqlite3"


def test_database_path_is_outside_the_user_library() -> None:
    library_dir = os.path.realpath(user_data_dir("PictoPy"))
    resolved = os.path.realpath(DATABASE_PATH)
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


def test_guard_follows_a_symlink_into_the_user_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library = tmp_path / "library"
    (library / "database").mkdir(parents=True)
    library_db = library / "database" / "PictoPy.db"
    library_db.touch()
    test_db = tmp_path / "test_db.sqlite3"
    test_db.symlink_to(library_db)
    monkeypatch.setattr(db_isolation, "user_data_dir", lambda _name: str(library))
    monkeypatch.setattr(db_isolation, "DATABASE_PATH", str(test_db))

    # SQLite follows the link, so comparing unresolved paths would let this through.
    with pytest.raises(RuntimeError, match="Refusing to run tests"):
        db_isolation._assert_not_user_library()
