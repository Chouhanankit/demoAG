import random
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)

# Algo state
price = 1000.0
entry_price = None
in_trade = False
total_pnl = 0.0
trade_count = 0

def algo_tick(sheet):
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

    row = [
        datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"),
        round(price, 2),
        action,
        pnl,
        round(total_pnl, 2),
        trade_count
    ]
    sheet.append_row(row, value_input_option="USER_ENTERED")
    logger.info(f"[{action}] Price={price:.2f} | PnL={pnl} | Total={total_pnl}")
