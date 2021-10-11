from datetime import datetime, timezone
from dateutil import parser
import logging

from environs import Env
from coincalc.cli import update_sheet

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
env = Env()


def coin(event, context):
    import base64

    timestamp = context.timestamp

    event_time = parser.parse(timestamp)
    event_age = (datetime.now(timezone.utc) - event_time).total_seconds()
    max_age_sec = 60 * 60 * 12
    if event_age > max_age_sec:
        logger.info('Dropped {} (age {}ms)'.format(context.event_id,
                                                   event_age))
        return 'Timeout'

    # Do what the function is supposed to do
    logger.info('Processed {} (age {}ms)'.format(context.event_id, event_age))

    request: str = ''
    if 'data' in event:
        request = base64.b64decode(event['data']).decode('utf-8')

    if request == 'update':
        logger.info("Received request")
        sheet_id = env("COIN_SHEET_ID")
        return update_sheet(sheet_id)
