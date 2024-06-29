import sqlite3
from typing import List, Tuple

def connectDB(dbPath: str) -> sqlite3.Connection:
    """Connects to the database at the given path.

    Args:
        dbPath: The path to the database file.

    Returns:
        A sqlite3.Connection object.
    """
    return sqlite3.connect(dbPath)

def createTable(conn: sqlite3.Connection, tableID: str, columns: List[str]) -> None:
    """Creates a table in the database with the given name and columns.

    Args:
        conn: A sqlite3.Connection object.
        tableID: The name of the table to create.
        columns: A list of column names.
    """
    query = f"CREATE TABLE IF NOT EXISTS {tableID} ({', '.join(columns)})"
    executeQuery(conn, query)

def executeQuery(conn: sqlite3.Connection, query: str, rowID: int = 0) -> List[Tuple]:
    """Executes a query on the database.

    Args:
        conn: A sqlite3.Connection object.
        query: The SQL query to execute.
        rowID: An optional integer indicating whether to return the last row ID.

    Returns:
        A list of tuples containing the results of the query, or the last row ID if rowID is 1.
    """
    cursor = conn.cursor()
    cursor.execute(query)
    if rowID == 1:
        return cursor.fetchall(), cursor.lastrowid
    return cursor.fetchall()
    # Prevent SQL injection (TBI)

def closeConnection(conn: sqlite3.Connection) -> None:
    """Closes the connection to the database.

    Args:
        conn: A sqlite3.Connection object.
    """
    conn.commit()
    conn.close()

def hashExist(conn: sqlite3.Connection, hashValue: str) -> bool:
    """Checks if a hash value exists in the database.

    Args:
        conn: A sqlite3.Connection object.
        hashValue: The hash value to check.

    Returns:
        True if the hash value exists, False otherwise.
    """
    query = f"SELECT EXISTS(SELECT 1 FROM media WHERE hash='{hashValue}')"
    result = executeQuery(conn, query)
    return result[0][0] == 1


def groupByclasses(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    """Returns hashes grouped by classes from the database.

    Args:
        conn: A sqlite3.Connection object.

    Returns:
        list: A list of tuples where each tuple contains class name and concatenated hashes.
        list[0][0]: class name
        list[0][1]: concatenated paths
    """
    query = """
        SELECT c.class, GROUP_CONCAT(i.path)
        FROM CLASS c
        JOIN JUNCTION j ON c.classID = j.classID
        JOIN IMAGES i ON j.imageID = i.imageID
        GROUP BY c.class
    """
    return executeQuery(conn, query)

def toggleVisibility(conn: sqlite3.Connection, paths: List[str], hidden: int) -> None:
    """Switch visibility of images by changing value of hidden column.

    Args:
        conn: sqlite3.Connection object.
        paths: A list of paths to switch visibility.
        hidden: The new value of hidden column.
    """
    query = f"UPDATE media SET hidden={hidden} WHERE path IN ({', '.join(['?'] * len(paths))})"
    executeQuery(conn, query, paths)

def hideByClass(conn: sqlite3.Connection, classes: List[str]) -> None:
    """Hides images by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A list of class names.
    """

def unhideByClass(conn: sqlite3.Connection, classes: List[str]) -> None:
    """Unhides images by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A list of class names.
    """

def delete(conn: sqlite3.Connection, paths: List[str]) -> None:
    """Prompt for confirmation.
    Deletes images by path.
    Deletes entry from DB considering junction table.

    Args:
        conn: sqlite3.Connection object.
        paths: A list of paths to delete.
    """

def deleteByClass(conn: sqlite3.Connection, classes: List[str]) -> None:
    """Deletes images by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A list of class names.
    """