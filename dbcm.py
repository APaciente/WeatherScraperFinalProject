"""
Program: Weather Processing App - Part 2 Database
Author: Arlo Paciente
Description:
    Simple context manager class (DBCM) for SQLite connections.

    Usage:
        from dbcm import DBCM

        with DBCM("weather.sqlite") as cur:
            cur.execute("SELECT 1;")
            rows = cur.fetchall()
"""

import sqlite3
from typing import Optional


class DBCM:
    """Context manager for SQLite connections.

    Opens a connection to the given database file, yields a cursor,
    and then commits on success or rolls back on error when exiting
    the with-block.
    """
    def __init__(self, filename: str):
        self.filename = filename
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def __enter__(self) -> sqlite3.Cursor:
        """Open the database and return a cursor."""
        self.conn = sqlite3.connect(self.filename)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Commit on success, roll back on error, then close connection.
        Returning False means any exception will still propagate.
        """
        if self.conn is None or self.cursor is None:
            return False

        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()

        self.cursor.close()
        self.conn.close()
        self.cursor = None
        self.conn = None

        return False
