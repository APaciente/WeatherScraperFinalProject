"""
Program: Weather Processing App - Part 3 Plotting
Author: Arlo Paciente
Description:
    PlotOperations takes rows fetched from the database and uses
    matplotlib to create:
      1) A boxplot of mean temperatures for each month over a
         user-specified year range.
      2) A line plot of daily mean temperatures for a specific
         month and year.

    Input rows are expected to come from DBOperations.fetch_data():
        (sample_date, min_temp, max_temp, avg_temp)
"""

from __future__ import annotations

from typing import Sequence, Tuple, Dict, List
import matplotlib.pyplot as plt

# Row format: (sample_date, min_temp, max_temp, avg_temp)
Row = Tuple[str, float, float, float]


class PlotOperations:
    """Helper class for plotting weather data using matplotlib.

    Takes database rows and can generate monthly boxplots and
    daily mean temperature line plots.
    """
    def __init__(self, rows: Sequence[Row]):
        """
        rows:
            Sequence of tuples: (sample_date, min_temp, max_temp, avg_temp)
            where sample_date is 'YYYY-MM-DD'.
        """
        # Copy to list so we can iterate more than once
        self.rows: List[Row] = list(rows)

    # ---------- internal helpers ----------

    def _build_monthly_mean_dict(
        self, start_year: int, end_year: int
    ) -> Dict[int, List[float]]:
        """
        Build a dictionary-of-lists for boxplotting.

        Returns:
            {
              1: [means for all January days between start_year and end_year],
              2: [means for all February days ...],
              ...
              12: [...]
            }
        """
        monthly: Dict[int, List[float]] = {m: [] for m in range(1, 13)}

        for sample_date, _min_t, _max_t, avg_t in self.rows:
            # sample_date is 'YYYY-MM-DD'
            year = int(sample_date[0:4])
            month = int(sample_date[5:7])

            if start_year <= year <= end_year:
                monthly[month].append(avg_t)

        return monthly

    def _get_daily_means_for_month(
        self, year: int, month: int
    ) -> Tuple[List[int], List[float]]:
        """
        Collects daily mean temperatures for a given year/month.

        Returns:
            (days, means)
            where 'days' is a list [1, 2, 3, ...] and 'means' matches.
        """
        days: List[int] = []
        means: List[float] = []

        for sample_date, _min_t, _max_t, avg_t in self.rows:
            y = int(sample_date[0:4])
            m = int(sample_date[5:7])
            if y == year and m == month:
                d = int(sample_date[8:10])
                days.append(d)
                means.append(avg_t)

        # Sort by day, just in case
        combined = sorted(zip(days, means), key=lambda pair: pair[0])
        if combined:
            days, means = zip(*combined)
            return list(days), list(means)

        return [], []

    # ---------- public plotting methods ----------

    def plot_monthly_boxplot(self, start_year: int, end_year: int) -> None:
        """
        Show a boxplot with one box per month, using mean daily
        temperatures between start_year and end_year (inclusive).
        """
        monthly_means = self._build_monthly_mean_dict(start_year, end_year)

        # Prepare data for matplotlib: list of 12 lists
        # Filter out months with no data so we don't crash,
        # but keep labels to show which months are present.
        data: List[List[float]] = []
        labels: List[int] = []

        for month in range(1, 13):
            values = monthly_means[month]
            if values:  # only plot months that have data
                data.append(values)
                labels.append(month)

        if not data:
            print("No data available for the requested year range.")
            return

        plt.figure()
        plt.boxplot(data, labels=labels)
        plt.xlabel("Month (1 = Jan, ... 12 = Dec)")
        plt.ylabel("Mean temperature (°C)")
        plt.title(f"Monthly Mean Temperature Distribution: {start_year}–{end_year}")
        plt.grid(True, axis="y", linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.show()

    def plot_daily_mean_line(self, year: int, month: int) -> None:
        """
        Show a line plot of daily mean temperatures for a specific
        month and year. X-axis is day-of-month, Y-axis is mean temp.
        """
        days, means = self._get_daily_means_for_month(year, month)

        if not days:
            print(f"No data available for {year}-{month:02d}.")
            return

        plt.figure()
        plt.plot(days, means, marker="o")
        plt.xlabel("Day of month")
        plt.ylabel("Mean temperature (°C)")
        plt.title(f"Mean Daily Temperature – {year}-{month:02d}")
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.show()
