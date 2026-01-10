import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
SELF_URL = os.getenv("SELF_URL")

logger = logging.getLogger(__name__)

def self_ping(interval=300):
    """Ping the app every `interval` seconds to keep it alive."""
    if not SELF_URL:
        logger.warning("SELF_URL not set, skipping self-ping")
        return

    while True:
        try:
            response = requests.get(SELF_URL + "/ping", timeout=5)
            if response.status_code == 200:
                logger.info("Self-ping successful")
            else:
                logger.warning(f"Self-ping returned {response.status_code}")
        except Exception as e:
            logger.error(f"Self-ping error: {e}")
        time.sleep(interval)
