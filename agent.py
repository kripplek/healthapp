# Run one of these on each server that needs to be monitored

import requests
import socket
import time
import logging
import os

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


def main():
    hostname = socket.gethostname()
    url = 'http://localhost:8000/api/v0/status/%s' % hostname
    interval = 60
    while True:
        start_time = time.time()
        try:
            r = requests.post(url)
            r.raise_for_status()
            logger.info('Posted status to %s successfully', url)
        except Exception:
						logger.exception('Failed posting')

        sleep_time = time.time() - start_time + 60

        logger.info('Sleeping %s until next iteration', sleep_time)
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
