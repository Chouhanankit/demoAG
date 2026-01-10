import os
import json
import time
import random
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials
import logging

# =========================
# CONFIG
# =========================
TICK_INTERVAL = 90
SHEET_NAME = "ALERT"
MAX_ROWS = 1000
TIMEZONE = ZoneInfo("Asia/Kolkata")

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
        logger.info("Using Google credentials from ENV")
        return json.loads(env_json)

    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set!")

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
# ALGO LOGIC
# =========================
def algo_tick(tick_time: datetime):
    global price, entry_price, in_trade, total_pnl, trade_count

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

    row = [
        tick_time.strftime("%Y-%m-%d %H:%M:%S"),
        round(price, 2),
        action,
        pnl,
        round(total_pnl, 2),
        trade_count
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")
    logger.info(f"[{action}] {tick_time} Price={price:.2f} PnL={pnl}")

# =========================
# CLOCK-SYNCED LOOP
# =========================
def market_loop():
    logger.info("🚀 Background Algo Started (Clock Synced)")

    now = datetime.now(TIMEZONE)
    next_tick = now - timedelta(
        seconds=now.timestamp() % TICK_INTERVAL
    ) + timedelta(seconds=TICK_INTERVAL)

    while True:
        sleep_seconds = (next_tick - datetime.now(TIMEZONE)).total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

        algo_tick(next_tick)
        next_tick += timedelta(seconds=TICK_INTERVAL)

# =========================
# ENTRY POINT 🔥
# =========================
if __name__ == "__main__":
    market_loop()
