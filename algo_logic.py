import random
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread

logger = logging.getLogger(__name__)
TIMEZONE = ZoneInfo("Asia/Kolkata")
MAX_ROWS = 1000

# =========================
# ALGO STATE
# =========================
price = 1000.0
entry_price = None
in_trade = False
total_pnl = 0.0
trade_count = 0

# =========================
# INIT SHEET
# =========================
sheet = None  # set by main.py

def set_sheet(gsheet):
    global sheet
    sheet = gsheet
    if sheet.cell(1, 1).value != "Timestamp":
        sheet.clear()
        sheet.append_row(
            ["Timestamp", "Price", "Action", "PnL", "Total_PnL", "Trade Count"]
        )

# =========================
# ALGO LOGIC FUNCTION
# =========================
def algo_tick():
    global price, entry_price, in_trade, total_pnl, trade_count

    if sheet is None:
        logger.warning("Sheet not set, skipping tick")
        return

    price += random.uniform(-2, 5)
    action = "NO_ACTION"
    pnl = 0.0

    # ENTRY
    if not in_trade and price > 1002:
        in_trade = True
        entry_price = price
        action = "BUY"
        trade_count += 1

    # EXIT
    elif in_trade:
        pnl = round((price - entry_price) * 10, 2)
        if pnl >= 80 or pnl <= -40:
            in_trade = False
            total_pnl += pnl
            action = "EXIT"

    # Ensure enough rows
    if sheet.row_count >= MAX_ROWS:
        sheet.add_rows(500)

    # Current timestamp
    current_time = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

    # Append row
    row = [
        current_time,
        round(price, 2),
        action,
        pnl,
        round(total_pnl, 2),
        trade_count
    ]
    try:
        sheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Failed to write to sheet: {e}")

    logger.info(f"[{action}] Price={price:.2f} | PnL={pnl} | Total={total_pnl}")
