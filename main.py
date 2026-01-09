import time
import random
import threading
from datetime import datetime

from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials

# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="Algo Demo with Google Sheet")

# =========================
# GOOGLE SHEET SETUP
# =========================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS = Credentials.from_service_account_file(
    "service_account.json",
    scopes=SCOPE
)

gc = gspread.authorize(CREDS)
sheet = gc.open("ALERT").sheet1


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

    # fake price movement
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

    # WRITE TO GOOGLE SHEET
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        round(price, 2),
        action,
        pnl,
        round(total_pnl, 2),
        trade_count
    ])

    print(f"[{action}] Price={price:.2f} | PnL={pnl} | Total={total_pnl}")


# =========================
# AUTO MARKET LOOP
# =========================
def market_loop():
    print("🚀 Auto Algo Started (Tick every 30 sec)")
    while True:
        algo_tick()
        time.sleep(30)


# =========================
# FASTAPI EVENTS
# =========================
@app.on_event("startup")
def start_algo():
    threading.Thread(target=market_loop, daemon=True).start()


@app.get("/")
def status():
    return {
        "status": "RUNNING",
        "price": round(price, 2),
        "in_trade": in_trade,
        "total_pnl": round(total_pnl, 2),
        "trade_count": trade_count
    }
