from datetime import datetime
import logging
import os.path

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from googleapiclient.discovery import build
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

API_BASE = 'https://www.coincalculators.io/api'


def fetch_coin_details(s: requests.Session, hashrate: int, power: float,
                       powercost: float) -> dict:
    retry_strat = Retry(
        total=20,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=2
    )
    s.mount('https://', HTTPAdapter(max_retries=retry_strat))
    params = {
        "hashrate": hashrate,
        "power": power,
        "powercost": powercost,
        "difficultytime": 24,
        "poolfee": "1",
        "name": "ethereum"
    }
    headers = {'Accept': 'application/json'}

    req = s.get(API_BASE, params=params, headers=headers)
    req.raise_for_status()

    return req.json()


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def fetch_creds() -> Credentials:
    creds: Credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    creds, program = google.auth.default(scopes=SCOPES)
    logger.info(f"Acquired credentials for program {program}")
    if not creds or not creds.valid:
        creds.refresh(Request())


    return creds


def add_row(sheet_id: str, creds: Credentials, row: list):
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet = {'properties': {'title': 'Ethereum Coin Tracker'}}
    sheet = service.spreadsheets()
    body = {'values': row}
    res = sheet.values().append(spreadsheetId=sheet_id,
                                range='Sheet1',
                                valueInputOption='USER_ENTERED',
                                insertDataOption='INSERT_ROWS',
                                body=body).execute()


def convert_megahash(ctx, param, value):
    return value * 1000000


# @click.command()
# @click.option('--sheet-id',
#               required = True,
#               help='Google Sheets Unique ID')
# @click.option('--hashrate',
#               default=62,
#               help="Hashrate in MH/s",
#               callback=convert_megahash,
#               type=int)
# @click.option('--wattage',
#               type=float,
#               default=130.0,
#               help='Wattage consumed by card')
# @click.option('--power-rate',
#               type=float,
#               default=0.122,
#               help="Power utility cost in killowatt/hr/dollar")
def update_sheet(sheet_id: str, hashrate: int = 62000000, wattage: float = 130.0, power_rate: float = 0.122):
    s = requests.Session()
    logger.info("Fetching coin details")
    coin_info = fetch_coin_details(s, hashrate, wattage, power_rate)
    logger.info("Coin details fetched successfully")
    columns = [
        'lastUpdate', 'rewardsInDay', 'revenueInDayUSD', 'profitInDayUSD'
    ]
    rows = [[coin_info.get(val) for val in columns]]
    # Adjust date
    rows[0][0] = datetime.fromtimestamp(rows[0][0] /
                                        1000.0).strftime('%Y-%m-%d %H:%M:%S')
    # Adjust eth profit based on power usage, etc
    eth_profit = coin_info.get('profitInDayUSD') / coin_info.get(
        'revenueInDayUSD') * coin_info.get('rewardsInDay')
    logger.info("Calculating ETH Profit")
    rows[0].extend([hashrate, wattage, power_rate, eth_profit])
    logger.info("Authenticating with Google APIs")
    creds = fetch_creds()
    logger.info("Posting data to google sheet")
    add_row(sheet_id, creds, rows)
    logger.info("All work completed!")
    return 'Successful Update'