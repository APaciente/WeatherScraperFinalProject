"""
Program: Weather Processing App - GUI Frontend (Bonus)
Author: Arlo Paciente
Description:
    Tkinter-based user interface for the Weather Processing App.
    Reuses the existing WeatherProcessor, database, and plotting code.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import date

from weather_processor import WeatherProcessor
from plot_operations import PlotOperations


class WeatherAppGUI:
    """Tkinter GUI wrapper around WeatherProcessor."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Weather Processing App")

        # Try a slightly more modern ttk theme
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Simple light theme colours
        self.bg_main = "#f5f5f7"
        self.bg_card = "#ffffff"
        self.bg_sidebar = "#f3f4f6"

        self.root.configure(bg=self.bg_main)

        style.configure("Sidebar.TFrame", background=self.bg_sidebar)
        style.configure("Main.TFrame", background=self.bg_main)
        style.configure("Card.TFrame", background=self.bg_card, relief="flat")

        style.configure(
            "Sidebar.TButton",
            font=("Segoe UI", 10),
            padding=(12, 8),
            anchor="w",
        )
        style.map("Sidebar.TButton", background=[("active", "#e5e7eb")])

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 16, "bold"),
            background=self.bg_main,
        )
        style.configure(
            "SidebarTitle.TLabel",
            font=("Segoe UI", 14, "bold"),
            background=self.bg_sidebar,
        )
        style.configure(
            "SectionTitle.TLabel",
            font=("Segoe UI", 12, "bold"),
            background=self.bg_card,
        )

        self.processor = WeatherProcessor()
        self._build_widgets()

    # ---------- UI construction ----------

    def _build_widgets(self) -> None:
        """Create and lay out all widgets."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, style="Main.TFrame", padding=0)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=0)  # sidebar
        main_frame.columnconfigure(1, weight=1)  # content
        main_frame.rowconfigure(0, weight=1)

        # ---------- Sidebar ----------
        sidebar = ttk.Frame(main_frame, style="Sidebar.TFrame", padding=16)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.configure(width=220)
        sidebar.columnconfigure(0, weight=1)

        sidebar_title = ttk.Label(
            sidebar,
            text="Weather Processing",
            style="SidebarTitle.TLabel",
        )
        sidebar_title.grid(row=0, column=0, sticky="w", pady=(0, 16))

        # Only global actions in the sidebar
        sidebar_buttons = [
            ("⬇  Full Download (Reset DB)", self.on_full_download),
            ("🔄  Update Data", self.on_update),
            ("📄  Summary Stats", self.on_summary),
            ("💾  Export to CSV", self.on_export),
        ]

        for i, (text, cmd) in enumerate(sidebar_buttons, start=1):
            btn = ttk.Button(
                sidebar,
                text=text,
                style="Sidebar.TButton",
                command=cmd,
            )
            btn.grid(row=i, column=0, sticky="ew", pady=4)

        # ---------- Content area ----------
        content = ttk.Frame(main_frame, style="Main.TFrame", padding=16)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        title_label = ttk.Label(content, text="Plot Settings", style="Title.TLabel")
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 12))

        cards_frame = ttk.Frame(content, style="Main.TFrame")
        cards_frame.grid(row=1, column=0, sticky="ew")
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)

        today = date.today()

        # ----- Monthly Boxplot card -----
        boxplot_card = ttk.Frame(cards_frame, style="Card.TFrame", padding=16)
        boxplot_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))

        boxplot_title = ttk.Label(
            boxplot_card, text="Monthly Boxplot", style="SectionTitle.TLabel"
        )
        boxplot_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(boxplot_card, text="Start Year:", background=self.bg_card).grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=4
        )
        self.start_year_var = tk.StringVar(value=str(today.year))
        self.start_year_entry = ttk.Entry(boxplot_card, textvariable=self.start_year_var)
        self.start_year_entry.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(boxplot_card, text="End Year:", background=self.bg_card).grid(
            row=2, column=0, sticky="e", padx=(0, 8), pady=4
        )
        self.end_year_var = tk.StringVar(value=str(today.year))
        self.end_year_entry = ttk.Entry(boxplot_card, textvariable=self.end_year_var)
        self.end_year_entry.grid(row=2, column=1, sticky="ew", pady=4)

        # Button lives inside the card
        run_boxplot_btn = ttk.Button(
            boxplot_card,
            text="Run Monthly Boxplot",
            command=self.on_boxplot,
        )
        run_boxplot_btn.grid(row=3, column=1, sticky="e", pady=(8, 0))

        boxplot_card.columnconfigure(1, weight=1)

        # ----- Daily Line Plot card -----
        line_card = ttk.Frame(cards_frame, style="Card.TFrame", padding=16)
        line_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))

        line_title = ttk.Label(
            line_card, text="Daily Line Plot", style="SectionTitle.TLabel"
        )
        line_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(line_card, text="Year:", background=self.bg_card).grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=4
        )
        self.line_year_var = tk.StringVar(value=str(today.year))
        self.line_year_entry = ttk.Entry(line_card, textvariable=self.line_year_var)
        self.line_year_entry.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(line_card, text="Month (1–12):", background=self.bg_card).grid(
            row=2, column=0, sticky="e", padx=(0, 8), pady=4
        )
        self.line_month_var = tk.StringVar(value=str(today.month))
        self.line_month_entry = ttk.Entry(line_card, textvariable=self.line_month_var)
        self.line_month_entry.grid(row=2, column=1, sticky="ew", pady=4)

        # Button lives inside the card
        run_lineplot_btn = ttk.Button(
            line_card,
            text="Run Daily Line Plot",
            command=self.on_lineplot,
        )
        run_lineplot_btn.grid(row=3, column=1, sticky="e", pady=(8, 0))

        line_card.columnconfigure(1, weight=1)

        # ----- Status card -----
        status_card = ttk.Frame(content, style="Card.TFrame", padding=16)
        status_card.grid(row=2, column=0, sticky="nsew")
        status_card.columnconfigure(0, weight=1)
        status_card.rowconfigure(1, weight=1)

        status_title = ttk.Label(
            status_card, text="Status / Messages", style="SectionTitle.TLabel"
        )
        status_title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.status_text = tk.Text(
            status_card,
            height=10,
            wrap="word",
            bd=0,
            relief="flat",
            background=self.bg_main,
        )
        self.status_text.grid(row=1, column=0, sticky="nsew")
        self.status_text.configure(state="disabled")

        self.append_status("Welcome to Weather Processing App")
        self.append_status("Select an action from the sidebar to begin")

    # ---------- helper for status messages ----------

    def append_status(self, message: str) -> None:
        """Append a message to the status text area."""
        self.status_text.configure(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")

    # ---------- button callbacks ----------

    def on_full_download(self) -> None:
        """Trigger a full DB reset + full scrape, with confirmation."""
        if not messagebox.askyesno(
            "Full Download",
            "This will reset the database and download the full history.\n\nContinue?",
        ):
            return

        self.append_status("Starting FULL download (reset DB)...")
        try:
            self.processor.download_full_history()
            self.append_status("Full download complete.")
        except Exception as exc:  # noqa: BLE001
            self.append_status(f"Error during full download: {exc}")
            messagebox.showerror("Error", f"Full download failed:\n{exc}")

    def on_update(self) -> None:
        """Update the database with any missing recent days."""
        self.append_status("Checking for updates...")
        try:
            self.processor.update_weather_data()
            self.append_status("Update complete (or already up to date).")
        except Exception as exc:  # noqa: BLE001
            self.append_status(f"Error during update: {exc}")
            messagebox.showerror("Error", f"Update failed:\n{exc}")

    def on_boxplot(self) -> None:
        """Run monthly boxplot using values from the card."""
        try:
            start_year = int(self.start_year_var.get())
            end_year = int(self.end_year_var.get())
        except ValueError:
            messagebox.showwarning(
                "Invalid input", "Please enter valid integers for start and end year."
            )
            return

        rows = self.processor.db.fetch_data()
        if not rows:
            msg = "No data in the database. Download first."
            self.append_status(f"Boxplot: {msg}")
            messagebox.showinfo("No data", msg)
            return

        # Pre-check: do we have any rows in this year range?
        has_data = any(
            start_year <= int(r[0][0:4]) <= end_year  # r[0] is 'YYYY-MM-DD'
            for r in rows
        )
        if not has_data:
            msg = "No data available for the requested year range."
            self.append_status(f"Boxplot: {msg}")
            messagebox.showinfo("No data", msg)
            return

        plotter = PlotOperations(rows)
        self.append_status(
            f"Showing monthly boxplot for {start_year} to {end_year}..."
        )
        try:
            plotter.plot_monthly_boxplot(start_year, end_year)
            self.append_status("Boxplot window opened.")
        except Exception as exc:  # noqa: BLE001
            self.append_status(f"Error creating boxplot: {exc}")
            messagebox.showerror("Error", f"Boxplot failed:\n{exc}")

    def on_lineplot(self) -> None:
        """Run daily line plot using values from the card."""
        try:
            year = int(self.line_year_var.get())
            month = int(self.line_month_var.get())
        except ValueError:
            messagebox.showwarning(
                "Invalid input", "Please enter valid integers for year and month."
            )
            return

        rows = self.processor.db.fetch_data()
        if not rows:
            msg = "No data in the database. Download first."
            self.append_status(f"Line plot: {msg}")
            messagebox.showinfo("No data", msg)
            return

        # Pre-check: is there any data for this year + month?
        has_data = any(
            int(r[0][0:4]) == year and int(r[0][5:7]) == month
            for r in rows
        )
        if not has_data:
            msg = f"No data available for {year}-{month:02d}."
            self.append_status(f"Line plot: {msg}")
            messagebox.showinfo("No data", msg)
            return

        plotter = PlotOperations(rows)
        self.append_status(f"Showing daily mean line for {year}-{month:02d}...")
        try:
            plotter.plot_daily_mean_line(year, month)
            self.append_status("Line plot window opened.")
        except Exception as exc:  # noqa: BLE001
            self.append_status(f"Error creating line plot: {exc}")
            messagebox.showerror("Error", f"Line plot failed:\n{exc}")

    def on_summary(self) -> None:
        """Show basic summary statistics for all stored weather data."""
        rows = self.processor.db.fetch_data()
        if not rows:
            self.append_status("Summary: no data in DB.")
            messagebox.showinfo("No data", "No data in the database yet.")
            return

        avg_temps = [r[3] for r in rows]

        min_temp = min(avg_temps)
        max_temp = max(avg_temps)
        avg_temp = sum(avg_temps) / len(avg_temps)

        msg = (
            "Summary statistics (all data):\n"
            f"  Number of days: {len(avg_temps)}\n"
            f"  Min mean temp: {min_temp:.1f} °C\n"
            f"  Max mean temp: {max_temp:.1f} °C\n"
            f"  Avg mean temp: {avg_temp:.1f} °C"
        )
        self.append_status(msg)
        messagebox.showinfo("Summary Statistics", msg)

    def on_export(self) -> None:
        """Export all DB rows to a CSV file."""
        rows = self.processor.db.fetch_data()
        if not rows:
            self.append_status("Export: no data in DB.")
            messagebox.showinfo("No data", "No data in the database to export.")
            return

        filename = "weather_export.csv"
        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["sample_date", "min_temp", "max_temp", "avg_temp"])
                writer.writerows(rows)
        except OSError as exc:
            self.append_status(f"Error writing to {filename}: {exc}")
            messagebox.showerror("Error", f"Export failed:\n{exc}")
            return

        self.append_status(f"Export complete. Saved to {filename}.")
        messagebox.showinfo("Export Complete", f"Data exported to {filename}.")


def main() -> None:
    """Launch the Tkinter GUI."""
    root = tk.Tk()
    WeatherAppGUI(root)
    root.minsize(900, 500)
    root.mainloop()


if __name__ == "__main__":
    main()
