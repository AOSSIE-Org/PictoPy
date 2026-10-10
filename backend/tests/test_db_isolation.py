import os

from platformdirs import user_data_dir

from app.database.connection import DATABASE_PATH


def test_queries_use_a_database_outside_the_user_library() -> None:
    # conftest checks the file name; this checks where the connection module's
    # copy of the path lands, resolving symlinks the way SQLite would.
    library_dir = os.path.realpath(user_data_dir("PictoPy"))
    resolved = os.path.realpath(DATABASE_PATH)
    assert os.path.commonpath([resolved, library_dir]) != library_dir
