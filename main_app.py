"""
Program: Weather Processing App - Main
Author: Arlo Paciente
Description:
    Main entry point for the Weather Processing App.
    Creates a WeatherProcessor instance and runs the full workflow.
"""

import logging
from weather_processor import WeatherProcessor

# Minimal logging setup for the whole app
logging.basicConfig(
    filename="weather_app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for the Weather Processing App."""
    logger.info("Weather app starting.")
    try:
        app = WeatherProcessor()
        app.run()
        logger.info("Weather app exited normally.")
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Unhandled error in main()")
        print("A fatal error occurred. Check weather_app.log for details.")


if __name__ == "__main__":
    main()
