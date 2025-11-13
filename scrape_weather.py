"""
Program: Weather Processing App - Part 1 Scraper
Author: Arlo Paciente

Description:
    Use Python's HTMLParser to scrape Winnipeg daily weather data
    (min, max, mean temperatures) from Environment Canada, starting
    from a URL encoded with today's year & month and walking backward
    month-by-month as far back as data is available.

    Output:
        {
            "YYYY-MM-DD": {"Max": float, "Min": float, "Mean": float},
            ...
        }

Rubric alignment:
  - scrape_weather.py module with a WeatherScraper class.
  - Uses HTMLParser to parse the site HTML.
  - Year & Month encoded directly in the URL.
  - Code walks backward and stops when no more weather data is available
    (no hard-coded last date, no dropdown scraping).
  - All scraping code is contained inside the WeatherScraper class.
"""

from __future__ import annotations

from html.parser import HTMLParser
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error

# ---------- helpers (non-scraping utilities) ----------
def _to_float(s: str) -> Optional[float]:
    """Convert string to float, treating special legend values / blanks as missing."""
    if not s:
        return None
    s = s.strip().replace("−", "-").replace("\u2212", "-")
    if s in {"LegendMM", "LegendEE", "M", "NA", "—", "-", ""}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _prev_year_month(y: int, m: int) -> Tuple[int, int]:
    """Return the previous calendar month."""
    return (y - 1, 12) if m == 1 else (y, m - 1)


# ---------- main scraper class ----------

class WeatherScraper:
    """
    Scrape Winnipeg daily weather data (max/min/mean temperature) from
    Environment Canada's Historical Climate Data site using HTMLParser.

    Typical usage:
        ws = WeatherScraper(start_url)
        weather = ws.scrape()

    Output format:
        {
            "YYYY-MM-DD": {"Max": float, "Min": float, "Mean": float},
            ...
        }
    """

    # Base URL pattern for Winnipeg A CS; year & month are filled in.
    # EndYear defaults to the current year and is always allowed.
    _BASE_URL = (
        "https://climate.weather.gc.ca/climate_data/daily_data_e.html"
        "?StationID=27174&timeframe=2&StartYear=1840&EndYear={end_year}"
        "&Day=1&Year={year}&Month={month}"
    )

    # ----- inner HTML parser for one month -----

    class _MonthWeatherParser(HTMLParser):
        """
        Parse the daily data table for a single month.

        Expected table columns (first four):
          0: day (1..31)
          1: Max temperature (°C)
          2: Min temperature (°C)
          3: Mean temperature (°C)

        Parsed rows are stored in self.weather as:
          {"YYYY-MM-DD": {"Max": float, "Min": float, "Mean": float}, ...}
        """

        def __init__(self, year: int, month: int):
            super().__init__()
            self.year = year
            self.month = month

            self.in_row = False
            self.in_cell = False
            self.row: List[str] = []
            self.cell_buf: List[str] = []

            self.weather: Dict[str, Dict[str, float]] = {}

        def handle_starttag(self, tag, attrs):
            # Start of a table row
            if tag == "tr":
                self.in_row = True
                self.row = []
            # Start of a cell (data or header) inside a row
            elif tag in ("td", "th") and self.in_row:
                self.in_cell = True
                self.cell_buf = []

        def handle_endtag(self, tag):
            # We reached the end of a cell: save its text
            if tag in ("td", "th") and self.in_cell:
                text = "".join(self.cell_buf).strip()
                self.row.append(text)
                self.in_cell = False

            # We reached the end of a row: decide if it's a real data row
            elif tag == "tr" and self.in_row:
                self._maybe_take_row(self.row)
                self.in_row = False
                self.row = []

        def handle_data(self, data):
            # Any text inside a cell gets buffered
            if self.in_cell:
                self.cell_buf.append(data)

        def _maybe_take_row(self, cells: List[str]) -> None:
            """If this is a real day row with numeric data, store it."""
            # Need at least Day, Max, Min, Mean
            if len(cells) < 4:
                return

            day_token = cells[0].strip()

            # Skip header/summary rows
            if day_token.upper() in {"DAY", "SUM", "AVG", "XTRM"}:
                return
            if day_token.startswith("Summary"):
                return

            # Must look like a day 1–31
            digits = "".join(ch for ch in day_token if ch.isdigit())
            if not digits:
                return
            try:
                day = int(digits)
            except ValueError:
                return
            if not (1 <= day <= 31):
                return

            max_v = _to_float(cells[1])
            min_v = _to_float(cells[2])
            mean_v = _to_float(cells[3])

            # Any missing temperature means we skip the day
            if None in (max_v, min_v, mean_v):
                return

            iso = f"{self.year:04d}-{self.month:02d}-{day:02d}"
            self.weather[iso] = {"Max": max_v, "Min": min_v, "Mean": mean_v}

    # ----- WeatherScraper methods -----

    def __init__(self, start_url: str, debug: bool = False):
        """
        start_url:
            Environment Canada daily_data_e.html URL with Year & Month
            encoded in the query string. Scraping walks backward from that
            year/month month-by-month until no more data is found.

        debug:
            If True, print progress while scraping.
        """
        self.start_url = start_url
        self.start_year, self.start_month = self._extract_year_month(start_url)
        self.debug = debug
        # Freeze the end year at construction time
        self._end_year = date.today().year

    @staticmethod
    def _extract_year_month(url: str) -> Tuple[int, int]:
        """
        Pull Year and Month from the query string.
        If missing or invalid, fall back to today's year and month.
        """
        try:
            qs = parse_qs(urlparse(url).query)
            year = int(qs.get("Year", [date.today().year])[0])
            month = int(qs.get("Month", [date.today().month])[0])
            if 1 <= month <= 12:
                return year, month
        except Exception:
            # Any parsing error falls through to default
            pass

        today = date.today()
        return today.year, today.month

    def _build_url(self, year: int, month: int) -> str:
        """Build the daily_data_e.html URL for a specific year/month."""
        return self._BASE_URL.format(
            year=year,
            month=month,
            end_year=self._end_year,
        )

    def _scrape_one_month(self, year: int, month: int) -> Dict[str, Dict[str, float]]:
        """
        Fetch one month page and parse it.

        Returns:
            Dict mapping YYYY-MM-DD -> {"Max": float, "Min": float, "Mean": float}
            for all days in that month that have valid numeric data.
            Empty dict means either no data or a network/HTTP problem.
        """
        url = self._build_url(year, month)
        if self.debug:
            print(f"Fetching month: {year}-{month:02d} -> {url}")

        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            if self.debug:
                print("  Network/HTTP error:", exc)
            return {}

        parser = self._MonthWeatherParser(year, month)
        parser.feed(html)
        parser.close()

        if self.debug:
            print(f"  Days parsed this month: {len(parser.weather)}")

        return parser.weather

    def scrape(self, max_months: int = 2400) -> Dict[str, Dict[str, float]]:
        """
        Walk backward month-by-month starting from the start_url's year/month
        until several consecutive empty months are seen.

        Args:
            max_months: Hard cap on months to prevent infinite loops
                        (default 2400 ≈ 200 years).

        Returns:
            Combined dict of all daily temperatures found.
        """
        all_weather: Dict[str, Dict[str, float]] = {}

        year, month = self.start_year, self.start_month
        empty_streak = 0

        for _ in range(max_months):
            month_data = self._scrape_one_month(year, month)

            if month_data:
                all_weather.update(month_data)
                empty_streak = 0
            else:
                empty_streak += 1
                if self.debug:
                    print(f"  Empty month streak = {empty_streak}")
                # After several consecutive empty months, assume we're past the
                # earliest available data and stop.
                if empty_streak >= 3:
                    break

            year, month = _prev_year_month(year, month)

        return all_weather


# ---------- simple manual test ----------

if __name__ == "__main__":
    # Build starting URL using today's year/month (assignment requirement).
    today = date.today()
    end_year = today.year

    start_url = WeatherScraper._BASE_URL.format(
        year=today.year,
        month=today.month,
        end_year=end_year,
    )

    scraper = WeatherScraper(start_url, debug=True)
    weather = scraper.scrape()

    if not weather:
        print("No weather data scraped. Check URL or parsing logic.")
    else:
        print(f"\nTotal days scraped: {len(weather)}")
        # Show a small sample
        for i, (day, temps) in enumerate(sorted(weather.items())):
            print(day, temps)
            if i >= 10:
                break

    input("\nPress Enter to finish...")
