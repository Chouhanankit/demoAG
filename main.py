import os
import json
import time
import threading
import logging
from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from algo_logic import algo_tick
from self_ping import self_ping

load_dotenv()
logger = logging.getLogger(__name__)

# -------------------------
# Google Sheets setup
# -------------------------
SHEET_NAME = "ALERT"
MAX_ROWS = 1000

def load_service_account():
    env_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_json:
        logger.info("Using GOOGLE_SERVICE_ACCOUNT_JSON from ENV")
        return json.loads(env_json)
    if os.path.exists("service_account.json"):
        logger.info("Using local service_account.json")
        with open("service_account.json") as f:
            return json.load(f)
    raise RuntimeError("Google service account not found!")

service_account_info = load_service_account()
CREDS = Credentials.from_service_account_info(service_account_info, scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
])
gc = gspread.authorize(CREDS)
sheet = gc.open(SHEET_NAME).sheet1
if sheet.cell(1, 1).value != "Timestamp":
    sheet.clear()
    sheet.append_row(["Timestamp", "Price", "Action", "PnL", "Total_PnL", "Trade Count"])

# -------------------------
# Background loops
# -------------------------
TICK_INTERVAL = 90

def market_loop():
    logger.info(f"🚀 Algo Loop Started")
    while True:
        algo_tick(sheet)
        time.sleep(TICK_INTERVAL)

# -------------------------
# FastAPI app
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=market_loop, daemon=True).start()
    threading.Thread(target=self_ping, daemon=True).start()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def status():
    return {"status": "RUNNING"}

@app.get("/ping")
def ping():
    return {"ping": "pong"}
