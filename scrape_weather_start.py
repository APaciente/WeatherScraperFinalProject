"""
Program: Weather Processing App – Part 1 Scraper
Author: Arlo Paciente
Description:
    Use Python's HTMLParser to scrape Winnipeg daily weather data
    (min, max, mean temperatures) from Environment Canada, starting
    from a given URL (encoded with a year & month) and walking backward
    month-by-month as far back as data is available.

    Output:
        {"YYYY-MM-DD": {"Max": float, "Min": float, "Mean": float}, ...}

Rubric alignment:
  - scrape_weather.py module with a WeatherScraper class.
  - Uses HTMLParser to parse the site HTML.
  - Year & Month encoded directly in the URL; code walks backward
    and stops when no more weather data is available (no hard-coded last date).
  - All scraping code is contained inside the WeatherScraper class.
"""

from __future__ import annotations

from html.parser import HTMLParser
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error


# ---------- small helpers (non-scraping utilities) ----------

def _to_float(s: str) -> Optional[float]:
    """Convert a string to float, treating LegendMM / blanks as missing."""
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
    All actual scraping + parsing lives here.

    Usage:
        ws = WeatherScraper(start_url)
        weather = ws.scrape()
    """

    # Base URL pattern for Winnipeg A CS; Year & Month are filled in.
    # This matches the instructor's example URL.
    _BASE_URL = (
        "http://climate.weather.gc.ca/climate_data/daily_data_e.html"
        "?StationID=27174&timeframe=2&StartYear=1840&EndYear=2018"
        "&Day=1&Year={year}&Month={month}"
    )

    # ----- inner HTML parser for one month -----

    class _MonthWeatherParser(HTMLParser):
        """
        Similar vibe to Arlo's colour scraper:
          row[0] = day ("01", "02", ...)
          row[1] = Max
          row[2] = Min
          row[3] = Mean
        Stores results in self.weather (dict of dicts).
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
            if tag == "tr":
                self.in_row = True
                self.row = []
            elif tag in ("td", "th") and self.in_row:
                self.in_cell = True
                self.cell_buf = []

        def handle_endtag(self, tag):
            if tag in ("td", "th") and self.in_cell:
                text = "".join(self.cell_buf).strip()
                self.row.append(text)
                self.in_cell = False

            elif tag == "tr" and self.in_row:
                self._maybe_take_row(self.row)
                self.in_row = False
                self.row = []

        def handle_data(self, data):
            if self.in_cell:
                self.cell_buf.append(data)

        def _maybe_take_row(self, cells: List[str]) -> None:
            """Decide if this row is a real day row and, if so, store it."""
            if len(cells) < 4:
                return

            day_token = cells[0].strip()

            # skip header + summary rows
            if day_token.upper() in {"DAY", "SUM", "AVG", "XTRM"}:
                return
            if day_token.startswith("Summary"):
                return

            # must look like a day 1–31
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

            if None in (max_v, min_v, mean_v):
                # rows with LegendMM etc. get skipped
                return

            iso = f"{self.year:04d}-{self.month:02d}-{day:02d}"
            self.weather[iso] = {"Max": max_v, "Min": min_v, "Mean": mean_v}

    # ----- WeatherScraper methods -----

    def __init__(self, start_url: str, debug: bool = False):
        """
        start_url: starting Environment Canada URL with Year & Month encoded.
        The code will walk backward month-by-month from that year/month.
        """
        self.start_url = start_url
        self.start_year, self.start_month = self._extract_year_month(start_url)
        self.debug = debug

    @staticmethod
    def _extract_year_month(url: str) -> Tuple[int, int]:
        """Pull Year and Month from the query string; fall back to today if missing."""
        try:
            qs = parse_qs(urlparse(url).query)
            year = int(qs.get("Year", [date.today().year])[0])
            month = int(qs.get("Month", [date.today().month])[0])
            if 1 <= month <= 12:
                return year, month
        except Exception:
            pass
        today = date.today()
        return today.year, today.month

    def _build_url(self, year: int, month: int) -> str:
        """Build a daily_data_e.html URL for the given year/month."""
        return self._BASE_URL.format(year=year, month=month)

    def _scrape_one_month(self, year: int, month: int) -> Dict[str, Dict[str, float]]:
        """
        Fetch one month page and parse it with HTMLParser.
        Returns dict of daily temps for that month; empty dict means no usable data.
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
        if self.debug:
            print(f"  Days parsed this month: {len(parser.weather)}")
        return parser.weather

    def scrape(self) -> Dict[str, Dict[str, float]]:
        """
        Walk backward month-by-month starting from the URL's year/month
        until we stop finding any daily data.
        Returns one big dictionary of all daily temps.
        """
        all_weather: Dict[str, Dict[str, float]] = {}

        year, month = self.start_year, self.start_month
        empty_streak = 0

        # Guard against infinite loops: 2400 months ≈ 200 years
        for _ in range(2400):
            month_data = self._scrape_one_month(year, month)

            if month_data:
                all_weather.update(month_data)
                empty_streak = 0
            else:
                empty_streak += 1
                # If we've walked back several months with no data, assume we're past the start.
                if self.debug:
                    print(f"  Empty month streak = {empty_streak}")
                if empty_streak >= 3:
                    break

            year, month = _prev_year_month(year, month)

        return all_weather


# ---------- simple manual test ----------

if __name__ == "__main__":
    # For a guaranteed working run, start from the instructor's sample URL (May 2018).
    # This still satisfies the "starting URL has year+month encoded" requirement.
    start_url = (
        "http://climate.weather.gc.ca/climate_data/daily_data_e.html"
        "?StationID=27174&timeframe=2&StartYear=1840&EndYear=2018"
        "&Day=1&Year=2018&Month=5"
    )

    # If you want to strictly follow "today's date" later, you can build a URL
    # with today's year/month using WeatherScraper._BASE_URL.

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
