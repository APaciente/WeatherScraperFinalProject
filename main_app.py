# main_app.py
from scrape_weather import WeatherScraper
from db_operations import DBOperations
from datetime import date

def main():
    # 1. Scrape
    today = date.today()
    start_url = WeatherScraper._BASE_URL.format(
        year=today.year,
        month=today.month,
        end_year=today.year,
    )
    scraper = WeatherScraper(start_url, debug=True)
    weather_dict = scraper.scrape(max_months=12)

    # 2. DB operations
    db = DBOperations("weather.sqlite", default_location="Winnipeg, MB")
    db.initialize_db()
    db.purge_data()
    db.save_data(weather_dict)

    # 3. Fetch for plotting
    rows = db.fetch_data()
    print(f"Total rows in DB: {len(rows)}")
    print("First 5 rows:", rows[:5])

if __name__ == "__main__":
    main()
