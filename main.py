import os
import json
import threading
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import gspread
from google.oauth2.service_account import Credentials

from algo_logic import algo_tick, set_sheet
from self_ping import start_self_ping

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================
TICK_INTERVAL = 90  # seconds
SHEET_NAME = "ALERT"
SELF_URL = os.getenv("SELF_URL")  # set your live URL here or in .env

# =========================
# GOOGLE SHEET AUTH
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def load_service_account():
    env_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        return json.loads(env_json)
    if os.path.exists("service_account.json"):
        with open("service_account.json", "r") as f:
            return json.load(f)
    raise RuntimeError("Google service account credentials not found!")

service_account_info = load_service_account()
CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
gc = gspread.authorize(CREDS)
sheet = gc.open(SHEET_NAME).sheet1

# Set sheet in algo logic
set_sheet(sheet)

# =========================
# BACKGROUND LOOPS
# =========================
def algo_loop():
    logger.info("🚀 Algo Loop Started")
    while True:
        algo_tick()
        import time; time.sleep(TICK_INTERVAL)

if SELF_URL:
    start_self_ping(SELF_URL)
else:
    logger.warning("SELF_URL not set, self-ping disabled")

# =========================
# FASTAPI APP
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=algo_loop, daemon=True).start()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def status():
    from algo_logic import price, in_trade, total_pnl, trade_count
    return {
        "status": "RUNNING",
        "price": round(price, 2),
        "in_trade": in_trade,
        "total_pnl": round(total_pnl, 2),
        "trade_count": trade_count
    }

@app.get("/ping")
def ping():
    return {"status": "alive"}
