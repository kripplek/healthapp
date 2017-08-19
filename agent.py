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


def bootstrap_key(api_url, key_path):
    hostname = socket.gethostname()

    if os.path.exists(key_path):
        try:
            with open(key_path, 'r') as h:
                return ujson.load(h)
        except:
            logger.exception('Failed loading %s', key_path)
            return False

    # Open file handle and bail here to avoid hitting the API prematurely
    with open(key_path, 'w') as key_file_handle:

        # Hit API to give us a key, which we will then hmac sign for all requests,
        # so the API knows who we are.
        url = '%s/api/v0/new_server/%s' % (api_url, hostname)
        try:
            r = requests.post(url)
            r.raise_for_status()
            data = r.json()
        except Exception:
            logger.exception('Failed registering with %s', api_url)
            return False

        logger.info('New server %s registered with API %s', hostname, api_url)

        credentials = {
            'hostname': hostname,
            'key': data['key']
        }

        ujson.dump(credentials, key_file_handle, indent=2)

    return credentials


def get_stats():
    return {}


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
    key_path = os.environ.get('KEY_PATH', 'agent_key.json')
    api_url = os.environ.get('API_URL', 'http://localhost:8000')

    credentials = bootstrap_key(api_url, key_path)

    if not credentials:
        logger.critical('Failed initializing')
        return

    api_key = str(credentials['key'])

    url = '%s/api/v0/status/%s' % (api_url, credentials['hostname'])
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
