import os
import json
import time
import random
import threading
from datetime import datetime
from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
import logging
from contextlib import asynccontextmanager

# =========================
# CONFIG
# =========================
TICK_INTERVAL = 90  # seconds
SHEET_NAME = "ALERT"
MAX_ROWS = 1000  # Google Sheet default limit

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# GOOGLE SHEET SETUP
# =========================
service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if not service_account_json:
    raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON is not set!")
service_account_info = json.loads(service_account_json)


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
gc = gspread.authorize(CREDS)

try:
    sheet = gc.open(SHEET_NAME).sheet1
except gspread.SpreadsheetNotFound:
    logger.error(f"Spreadsheet '{SHEET_NAME}' not found! Create it first.")
    raise

# Set headers if empty
if sheet.row_count == 0 or sheet.cell(1, 1).value != "Timestamp":
    sheet.clear()
    sheet.append_row(["Timestamp", "Price", "Action", "PnL", "Total_PnL", "Trade Count"])
    logger.info("Sheet headers created.")

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
def algo_tick():
    global price, entry_price, in_trade, total_pnl, trade_count

    # simulate price movement
    price += random.uniform(-2, 5)
    action = "NO_ACTION"
    pnl = 0.0

    # ENTRY LOGIC
    if not in_trade and price > 1002:
        in_trade = True
        entry_price = price
        action = "BUY"
        trade_count += 1

    # EXIT LOGIC
    elif in_trade:
        pnl = round((price - entry_price) * 10, 2)
        if pnl >= 80 or pnl <= -40:
            in_trade = False
            total_pnl += pnl
            action = "EXIT"

    # Ensure Google Sheet has enough rows
    if sheet.row_count >= MAX_ROWS:
        sheet.add_rows(500)

    # Append data to sheet
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        round(price, 2),
        action,
        pnl,
        round(total_pnl, 2),
        trade_count
    ]
    try:
        sheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Failed to write to Google Sheet: {e}")

    logger.info(f"[{action}] Price={price:.2f} | PnL={pnl} | Total={total_pnl}")

# =========================
# MARKET LOOP
# =========================
def market_loop():
    logger.info(f"🚀 Auto Algo Started (Tick every {TICK_INTERVAL} sec)")
    while True:
        try:
            algo_tick()
        except Exception as e:
            logger.error(f"Algo tick error: {e}")
        time.sleep(TICK_INTERVAL)

# =========================
# FASTAPI APP
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=market_loop, daemon=True).start()
    yield

app = FastAPI(title="Algo Demo with Google Sheet", lifespan=lifespan)

@app.get("/")
def status():
    return {
        "status": "RUNNING",
        "price": round(price, 2),
        "in_trade": in_trade,
        "total_pnl": round(total_pnl, 2),
        "trade_count": trade_count
    }
