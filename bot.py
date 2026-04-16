import logging
from adapters.telegram.telegram_bot import start_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    logging.getLogger(__name__).info("Iniciando Strava Bot")
    start_bot()
    