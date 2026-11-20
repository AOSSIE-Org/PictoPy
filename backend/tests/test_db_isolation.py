from pathlib import Path

from platformdirs import user_data_dir

from app.database.connection import DATABASE_PATH


def test_queries_use_a_database_outside_the_user_library() -> None:
    # conftest checks the file name; this checks where the connection module's
    # copy of the path lands, resolving symlinks the way SQLite would.
    library_dir = Path(user_data_dir("PictoPy")).resolve()
    resolved = Path(DATABASE_PATH).resolve()
    # is_relative_to, unlike os.path.commonpath, does not raise across Windows drives.
    assert not resolved.is_relative_to(library_dir)
