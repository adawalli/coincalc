import logging

from environs import Env
from coincalc.cli import update_sheet

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
env = Env()

def coin(request):
    logger.info("Received request")
    sheet_id = env("COIN_SHEET_ID")
    return update_sheet(sheet_id)