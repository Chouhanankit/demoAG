import os
import json
import time
import random
import threading
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
import logging
from contextlib import asynccontextmanager

# =========================
# CONFIG
# =========================
TICK_INTERVAL = 90
SHEET_NAME = "ALERT"
MAX_ROWS = 1000
TIMEZONE = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# GOOGLE AUTH
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def load_service_account():
    env_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        logger.info("Using GOOGLE_SERVICE_ACCOUNT_JSON from ENV")
        return json.loads(env_json)

    if os.path.exists("service_account.json"):
        logger.info("Using local service_account.json")
        with open("service_account.json", "r") as f:
            return json.load(f)

    raise RuntimeError("Google service account credentials not found!")

service_account_info = load_service_account()

CREDS = Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

gc = gspread.authorize(CREDS)
sheet = gc.open(SHEET_NAME).sheet1

# =========================
# SHEET INIT
# =========================
if sheet.cell(1, 1).value != "Timestamp":
    sheet.clear()
    sheet.append_row(
        ["Timestamp", "Price", "Action", "PnL", "Total_PnL", "Trade Count"]
    )

# =========================
# ALGO STATE
# =========================
price = 1000.0
entry_price = None
in_trade = False
total_pnl = 0.0
trade_count = 0

# =========================
# MARKET TIME CHECK
# =========================
def is_market_open():
    now = datetime.now(TIMEZONE)
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE

# =========================
# ALGO LOGIC
# =========================
def algo_tick():
    global price, entry_price, in_trade, total_pnl, trade_count

    if not is_market_open():
        logger.info("⏸ Market Closed — Algo Idle")
        return

    price += random.uniform(-2, 5)
    action = "NO_ACTION"
    pnl = 0.0

    if not in_trade and price > 1002:
        in_trade = True
        entry_price = price
        action = "BUY"
        trade_count += 1

    elif in_trade:
        pnl = round((price - entry_price) * 10, 2)
        if pnl >= 80 or pnl <= -40:
            in_trade = False
            total_pnl += pnl
            action = "EXIT"

    if sheet.row_count >= MAX_ROWS:
        sheet.add_rows(500)

    timestamp = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        round(price, 2),
        action,
        pnl,
        round(total_pnl, 2),
        trade_count
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")
    logger.info(f"[{action}] {timestamp} Price={price:.2f} PnL={pnl}")

# =========================
# BACKGROUND LOOP
# =========================
def market_loop():
    logger.info("🚀 Background Algo Started (Market Time Filter ON)")
    while True:
        try:
            algo_tick()
        except Exception as e:
            logger.error(f"Algo error: {e}")
        time.sleep(TICK_INTERVAL)

# =========================
# FASTAPI
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=market_loop, daemon=True).start()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def status():
    return {
        "status": "RUNNING",
        "market_open": is_market_open(),
        "price": round(price, 2),
        "in_trade": in_trade,
        "total_pnl": round(total_pnl, 2),
        "trade_count": trade_count
    }
