"""
Program: Weather Scraper – Simple Debug Version
Author: Arlo Paciente
Description:
    Fetch ONE daily-data page from Environment Canada and use HTMLParser
    to print every table row (<tr>) as a list of cell texts.
    This is just for debugging the HTML structure – no DB, no looping.
"""
from html.parser import HTMLParser
import urllib.request
from typing import Dict, List, Optional

URL = (
    "http://climate.weather.gc.ca/climate_data/daily_data_e.html"
    "?StationID=27174&timeframe=2&StartYear=1840&EndYear=2018"
    "&Day=1&Year=2018&Month=5"
)


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


class MonthWeatherParser(HTMLParser):
    """
    Similar vibe to your colour scraper:
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

def get_month_weather() -> Dict[str, Dict[str, float]]:
    """Like get_colours(): fetch page, feed parser, return dict."""
    with urllib.request.urlopen(URL) as response:
        html = response.read().decode("utf-8", errors="ignore")

    parser = MonthWeatherParser(year=2018, month=5)
    parser.feed(html)
    return parser.weather


if __name__ == "__main__":
    weather = get_month_weather()

    if not weather:
        print("No weather data parsed. Check parsing logic.")
    else:
        for i, (day, temps) in enumerate(sorted(weather.items())):
            print(day, temps)
            if i >= 10:
                break
        print(f"\nTotal days parsed: {len(weather)}")

    input("\nPress Enter to finish...")
