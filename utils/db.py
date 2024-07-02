import sqlite3
from typing import List, Tuple, Dict
from utils.fs import deleteFile

def connectDB(dbPath: str) -> sqlite3.Connection:
    """Connects to the database at the given path.

    Args:
        dbPath: The path to the database file.

    Returns:
        A sqlite3.Connection object.
    """
    return sqlite3.connect(dbPath)

def createTable(conn: sqlite3.Connection, tableID: str, columns: Tuple[str]) -> None:
    """Creates a table in the database with the given name and columns.

    Args:
        conn: A sqlite3.Connection object.
        tableID: The name of the table to create.
        columns: A tuple of column names.
    """
    query = f"CREATE TABLE IF NOT EXISTS {tableID} ({', '.join(columns)})"
    executeQuery(conn, query)

def executeQuery(conn: sqlite3.Connection, query: str, rowID: int = 0) -> List[Tuple]:
    """Executes a query on the database.
    Prevent SQL injection (TBI)

    Args:
        conn: A sqlite3.Connection object.
        query: The SQL query to execute.
        rowID: An optional integer indicating whether to return the last row ID.

    Returns:
        A tuple of tuples containing the results of the query, or the last row ID if rowID is 1.
    """
    cursor = conn.cursor()
    cursor.execute(query)
    if rowID == 1:
        return cursor.fetchall(), cursor.lastrowid
    return cursor.fetchall()

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
    query = f"SELECT EXISTS(SELECT 1 FROM MEDIA WHERE hash='{hashValue}')"
    result = executeQuery(conn, query)
    return result[0][0] == 1


def groupByClass(conn: sqlite3.Connection, hidden: int = 0, groupOf: str = "path") -> Dict[str, Tuple[str]]:
    """Returns paths grouped by classes from the database.

    Args:
        conn: A sqlite3.Connection object.
        groupOf: The column to be grouped.

    Returns:
        dict: A dictionary where each key is a class name and each value is a tuple of paths.
    """
    query = f"""
        SELECT c.class, GROUP_CONCAT(i.{groupOf})
        FROM CLASS c
        JOIN JUNCTION j ON c.classID = j.classID 
        JOIN MEDIA i ON j.imageID = i.imageID WHERE i.hidden = {hidden}
        GROUP BY c.class
    """
    dict = {}
    for row in executeQuery(conn, query):
        dict[row[0]] = tuple(row[1].split(','))
    return dict

def toggleVisibility(conn: sqlite3.Connection, paths: Tuple[str], hidden: int) -> None:
    """Switch visibility of images by changing value of hidden column.

    Args:
        conn: sqlite3.Connection object.
        paths: A tuple of paths to switch visibility.
        hidden: The new value of hidden column.
    """
    query = f"UPDATE MEDIA SET hidden={hidden} WHERE path IN {paths}"
    executeQuery(conn, query)

def tupleByClass(conn: sqlite3.Connection, classes: Tuple[str], hidden: int = 0, groupOf: str = "path") -> Tuple[str]:
    """Returns tuple of all paths associated with the given classes.
    (TBI) improve efficiency, as groupByClass() scans whole DB which is expensive.

    Args:
        conn: sqlite3.Connection object.
        classes: A tuple of class names.
        groupOf: The column to be grouped.

    Returns:
        A tuple of paths.
    """
    res = []
    groups = groupByClass(conn, hidden, groupOf)
    for class_ in groups:
        if class_ in classes:
            res.extend(groups[class_])
    return tuple(res)

def hideByClass(conn: sqlite3.Connection, classes: Tuple[str]) -> None:
    """Hides images by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A tuple of class names.
    """
    toggleVisibility(conn, tupleByClass(conn, classes, 0), 1)
    
def unhideByClass(conn: sqlite3.Connection, classes: Tuple[str]) -> None:
    """Unhides images by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A tuple of class names.
    """
    toggleVisibility(conn, tupleByClass(conn, classes, 1), 0)

def deleteFromDB(conn: sqlite3.Connection, paths: Tuple[str]) -> None:
    """
    Delete related rows from DB. 
    Delete files by path.

    Args:
        conn: sqlite3.Connection object.
        paths: A tuple of paths to delete.
    """
    query = f"DELETE FROM MEDIA WHERE path IN {paths}"
    executeQuery(conn, query)
    deleteFile(paths)

def deleteByClass(conn: sqlite3.Connection, classes: Tuple[str]) -> None:
    """Deletes images by class.

    Args:
        conn: sqlite3.Connection object.
        classes: A tuple of class names.
    """
    delete(conn, tupleByClass(conn, classes))