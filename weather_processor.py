"""
Program: Weather Processing App - Part 4 User Interaction
Author: Arlo Paciente
Description:
    WeatherProcessor is the main controller for the app.
    It:
      - Lets the user download a full set of weather data.
      - Lets the user update the database with only the missing
        days between the latest DB date and today.
      - Lets the user enter a year range to generate a box plot.
      - Lets the user enter a year + month to generate a line plot.
      - Lets the user view summary statistics.
      - Lets the user export data to CSV.
      - Contains ALL user interaction / menus.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
import csv

from scrape_weather import WeatherScraper
from db_operations import DBOperations
from plot_operations import PlotOperations


class WeatherProcessor:
    """Main controller for the Weather Processing App.

    Handles user interaction, scraping, database updates, and plotting.
    """

    def __init__(self, db_name: str = "weather.sqlite", location: str = "Winnipeg, MB"):
        self.db = DBOperations(db_name, default_location=location)

    # ---------- public entrypoint ----------

    def run(self) -> None:
        """Main menu loop. All user interaction lives here."""
        # Make sure DB and table exist
        self.db.initialize_db()

        while True:
            print("\n=== Weather Processing App ===")
            print("1. Download FULL weather history (reset DB)")
            print("2. Update weather data up to today")
            print("3. Plot monthly boxplot (year range)")
            print("4. Plot daily mean line (specific month/year)")
            print("5. Show summary statistics")
            print("6. Export data to CSV")
            print("7. Exit")

            choice = input("Enter your choice (1-7): ").strip()

            if choice == "1":
                self.download_full_history()
            elif choice == "2":
                self.update_weather_data()
            elif choice == "3":
                self.plot_boxplot_menu()
            elif choice == "4":
                self.plot_line_menu()
            elif choice == "5":
                self.show_summary_stats()
            elif choice == "6":
                self.export_to_csv()
            elif choice == "7":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number 1–7.")

    # ---------- internal helpers ----------

    def _build_today_start_url(self) -> str:
        """Build a start URL using today's year/month."""
        today = date.today()
        return WeatherScraper._BASE_URL.format(
            year=today.year,
            month=today.month,
            end_year=today.year,
        )

    def _make_plotter(self) -> Optional[PlotOperations]:
        """Fetch rows from DB and create a PlotOperations, or None if DB empty."""
        rows = self.db.fetch_data()
        if not rows:
            print("No data in the database yet. Download data first.")
            return None
        return PlotOperations(rows)

    # ---------- menu actions ----------

    def download_full_history(self) -> None:
        """
        Completely refresh the database with a full set of weather data.
        Scrapes from today backward until no more data is available.
        """
        print("\nDownloading FULL weather history (this may take a while)...")
        start_url = self._build_today_start_url()
        scraper = WeatherScraper(start_url, debug=True)

        # Full scrape: no max_months limit
        weather_dict = scraper.scrape()

        print(f"Days scraped: {len(weather_dict)}. Saving to database...")
        self.db.purge_data()  # remove old rows but keep table
        inserted = self.db.save_data(weather_dict)
        print(f"Done. Rows attempted to insert: {inserted}")

    def update_weather_data(self) -> None:
        """
        Update the database with any missing days between the last
        date in the DB and today's date, without duplicating data.
        """
        print("\nChecking for updates...")

        rows = self.db.fetch_data()
        if not rows:
            print("Database is empty. Running full download instead.")
            self.download_full_history()
            return

        # Latest date currently stored in DB
        latest_date_str = max(r[0] for r in rows)  # r[0] = sample_date 'YYYY-MM-DD'
        latest_date = date.fromisoformat(latest_date_str)
        today = date.today()

        if latest_date >= today:
            print(f"Data is already up to date (through {latest_date_str}).")
            return

        # How many months do we need to scrape to cover latest_date -> today?
        months_needed = (
            (today.year - latest_date.year) * 12
            + (today.month - latest_date.month)
            + 1
        )

        print(
            f"Updating from {latest_date_str} to {today.isoformat()} "
            f"(approx. {months_needed} months of data)..."
        )

        start_url = self._build_today_start_url()
        scraper = WeatherScraper(start_url, debug=True)
        new_weather = scraper.scrape(max_months=months_needed)

        # Keep only days AFTER the latest date in DB
        to_save = {d: temps for d, temps in new_weather.items() if d > latest_date_str}

        if not to_save:
            print("No new days found to add.")
            return

        inserted = self.db.save_data(to_save)
        print(f"Update complete. New days added: {inserted}")

    def plot_boxplot_menu(self) -> None:
        """Prompt for year range and generate boxplot."""
        plotter = self._make_plotter()
        if plotter is None:
            return

        today = date.today()

        try:
            start_text = input(f"Enter start year (default {today.year}): ").strip()
            end_text = input(f"Enter end year   (default {today.year}): ").strip()

            start_year = int(start_text) if start_text else today.year
            end_year = int(end_text) if end_text else today.year
        except ValueError:
            print("Invalid year entered. Using current year only.")
            start_year = end_year = today.year

        plotter.plot_monthly_boxplot(start_year, end_year)

    def plot_line_menu(self) -> None:
        """Prompt for year/month and generate line plot."""
        plotter = self._make_plotter()
        if plotter is None:
            return

        today = date.today()

        try:
            year_text = input(f"Enter year (default {today.year}): ").strip()
            month_text = input(
                f"Enter month 1–12 (default {today.month}): "
            ).strip()

            year = int(year_text) if year_text else today.year
            month = int(month_text) if month_text else today.month
        except ValueError:
            print("Invalid input. Using current year/month.")
            year = today.year
            month = today.month

        plotter.plot_daily_mean_line(year, month)

    def show_summary_stats(self) -> None:
        """Print simple summary statistics for all data in the database."""
        rows = self.db.fetch_data()
        if not rows:
            print("No data in the database yet.")
            return

        # avg_temp is index 3 in (sample_date, min_temp, max_temp, avg_temp)
        avg_temps = [r[3] for r in rows]

        min_temp = min(avg_temps)
        max_temp = max(avg_temps)
        avg_temp = sum(avg_temps) / len(avg_temps)

        print("\nSummary statistics (all data):")
        print(f"  Number of days: {len(avg_temps)}")
        print(f"  Min mean temp: {min_temp:.1f} °C")
        print(f"  Max mean temp: {max_temp:.1f} °C")
        print(f"  Avg mean temp: {avg_temp:.1f} °C")

    def export_to_csv(self) -> None:
        """Export all weather rows from the database to a CSV file."""
        rows = self.db.fetch_data()
        if not rows:
            print("No data in the database to export.")
            return

        filename = "weather_export.csv"
        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["sample_date", "min_temp", "max_temp", "avg_temp"])
                writer.writerows(rows)
        except OSError as exc:
            print(f"Error writing to {filename}: {exc}")
            return

        print(f"Export complete. Saved to {filename}.")
