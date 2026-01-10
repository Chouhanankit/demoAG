import time
import threading
import requests
import logging

logger = logging.getLogger(__name__)

def start_self_ping(url, interval_sec=240):
    """Ping your app URL every interval_sec to keep alive."""
    def ping_loop():
        while True:
            try:
                resp = requests.get(url, timeout=10)
                logger.info(f"Self-ping {url} | Status: {resp.status_code}")
            except Exception as e:
                logger.error(f"Self-ping error: {e}")
            time.sleep(interval_sec)

    thread = threading.Thread(target=ping_loop, daemon=True)
    thread.start()
