# Run one of these on each server that needs to be monitored

import requests
import socket
import time
import logging
import ujson
import os
import hmac
import hashlib
import base64
import platform
from config import process_config

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
log_file = os.environ.get('LOG_FILE')
if log_file:
    ch = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10485760, backupCount=10)
else:
    ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(ch)


def get_stats():
    return {
        'OS': platform.system(),
        'Kernel': platform.release()
    }


def generate_payload(stats, api_key):
    body = ujson.dumps(stats)
    hmac_obj = hmac.new(api_key, body, hashlib.sha512)
    headers = {
        'X-INTEGRITY': base64.urlsafe_b64encode(hmac_obj.digest())
    }
    return {
        'body': body,
        'headers': headers
    }


def main():
    configs = process_config()

    api_url = configs.get('api_url', 'http://localhost:8000')
    api_key = configs.get('api_key')

    if not api_key:
        logger.critical('no api_key found in config')
        return

    api_key = str(api_key)
    hostname = socket.gethostname()

    url = '%s/api/v0/status/%s' % (api_url, hostname)
    interval = 60
    while True:
        payload = generate_payload(get_stats(), api_key)
        try:
            r = requests.post(url, data=payload['body'], headers=payload['headers'])
            r.raise_for_status()
            logger.info('Posted status to %s successfully', url)
        except Exception:
            logger.exception('Failed posting')

        logger.info('Sleeping %s until next iteration', interval)
        time.sleep(interval)


if __name__ == '__main__':
    main()
