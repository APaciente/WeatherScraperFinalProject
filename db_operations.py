"""
Program: Weather Processing App - Part 2 Database
Author: Arlo Paciente
Description:
    Define a DBOperations class that uses sqlite3 (via the DBCM context
    manager) to store weather data in an SQLite database.

    Table schema:
        id          -> integer, primary key, autoincrement
        sample_date -> text, unique in combination with location
        location    -> text, unique in combination with sample_date
        min_temp    -> real
        max_temp    -> real
        avg_temp    -> real

    Input to save_data():
        Dictionary from WeatherScraper:
            {
              "YYYY-MM-DD": {"Max": float, "Min": float, "Mean": float},
              ...
            }

    Output from fetch_data():
        A tuple of rows containing DB records, suitable for plotting.
"""

from __future__ import annotations

from typing import Dict, Tuple, List
from dbcm import DBCM


class DBOperations:
    """High-level helper for creating, clearing, saving, and fetching
    weather data in an SQLite database.
    """
    def __init__(self, db_name: str, default_location: str = "Winnipeg, MB"):
        """
        db_name:
            Path/filename of the SQLite database.

        default_location:
            Location string used when saving data, unless overridden.
        """
        self.db_name = db_name
        self.default_location = default_location

    # ---------- schema / housekeeping ----------

    def initialize_db(self) -> None:
        """
        Create the weather_data table if it doesn't already exist.
        Should be called every time the program starts.
        """
        with DBCM(self.db_name) as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_data (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    sample_date TEXT    NOT NULL,
                    location    TEXT    NOT NULL,
                    min_temp    REAL    NOT NULL,
                    max_temp    REAL    NOT NULL,
                    avg_temp    REAL    NOT NULL,
                    UNIQUE(sample_date, location)
                );
                """
            )

    def purge_data(self) -> None:
        """
        Delete all rows from the weather_data table (but not the table itself).
        Used when re-scraping all new weather data.
        """
        with DBCM(self.db_name) as cur:
            cur.execute("DELETE FROM weather_data;")

    # ---------- insert / save ----------

    def save_data(
        self,
        weather_dict: Dict[str, Dict[str, float]],
        location: str | None = None,
    ) -> int:
        """
        Save scraped weather data into the database.

        weather_dict:
            The dictionary returned by WeatherScraper.scrape().

        location:
            Optional location label; if omitted, uses default_location.

        Uses INSERT OR IGNORE together with the UNIQUE(sample_date, location)
        constraint to avoid duplicate rows.

        Returns:
            The number of rows attempted to insert (not necessarily the number
            actually inserted, because duplicates are ignored).
        """
        loc = location or self.default_location

        rows_to_insert: List[Tuple[str, str, float, float, float]] = []

        for date_str, metrics in weather_dict.items():
            try:
                max_temp = float(metrics["Max"])
                min_temp = float(metrics["Min"])
                avg_temp = float(metrics["Mean"])
            except (KeyError, TypeError, ValueError):
                # Skip any bad record rather than crashing
                continue

            rows_to_insert.append((date_str, loc, min_temp, max_temp, avg_temp))

        if not rows_to_insert:
            return 0

        with DBCM(self.db_name) as cur:
            cur.executemany(
                """
                INSERT OR IGNORE INTO weather_data
                    (sample_date, location, min_temp, max_temp, avg_temp)
                VALUES (?, ?, ?, ?, ?);
                """,
                rows_to_insert,
            )
            # rowcount is "attempted" inserts; duplicates are ignored by SQLite
            return cur.rowcount

    # ---------- fetch for plotting ----------

    def fetch_data(self, location: str | None = None) -> Tuple[Tuple]:
        """
        Fetch weather data from the database for plotting.

        location:
            Optional filter by location. If None, uses default_location.

        Returns:
            A tuple of rows. Each row is:
                (sample_date, min_temp, max_temp, avg_temp)
        """
        loc = location or self.default_location

        with DBCM(self.db_name) as cur:
            cur.execute(
                """
                SELECT sample_date, min_temp, max_temp, avg_temp
                FROM weather_data
                WHERE location = ?
                ORDER BY sample_date;
                """,
                (loc,),
            )
            result_rows = cur.fetchall()

        # Convert list of rows to tuple of rows (as per assignment)
        return tuple(result_rows)


# ---------- simple manual test ----------

if __name__ == "__main__":
    # Small fake dataset like your CSV assignment
    sample_weather = {
        "2018-06-01": {"Max": 12.0, "Min": 5.6, "Mean": 7.1},
        "2018-06-02": {"Max": 22.2, "Min": 11.1, "Mean": 15.5},
        "2018-06-03": {"Max": 31.3, "Min": 29.9, "Mean": 30.0},
    }

    db = DBOperations("weather.sqlite", default_location="Winnipeg, MB")

    # Initialize, purge, save, fetch, and print a few rows
    db.initialize_db()
    db.purge_data()
    inserted = db.save_data(sample_weather)
    print(f"Rows attempted to insert: {inserted}")

    rows = db.fetch_data()
    print("Rows fetched from DB:")
    for row in rows:
        print(row)
