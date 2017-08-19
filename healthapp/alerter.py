# stateful service which monitors server status in redis
# and keeps track of alerts and alerting

import redis
import time
import uuid
import logging
import os
from datetime import datetime
from collections import defaultdict

from constants import key_map, default_alert_process_interval, default_server_staleness_duration
from notify import notify_alert_new, notify_alert_closed, notify_ongoing_alert
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


def get_bad_states(r, server_staleness_duration):
    bad_states = {}

    good_time = int(time.time() - server_staleness_duration)
    for server, value in r.zrevrangebyscore(key_map['server_last_posts'], good_time, 0, score_cast_func=int, withscores=True):
        key = 'stale_%s' % server
        bad_states[key] = {
            'info': 'Server %s last reported on %s' % (server, datetime.fromtimestamp(value))
        }

    return bad_states


def generate_alert_id(state_name):
    return '%s_%s' % (state_name, uuid.uuid4())


def create_alert(r, state_name, description):
    now = time.time()
    alert_id = generate_alert_id(state_name)

    description['start_time'] = now
    description['end_time'] = -1
    description['state_name'] = state_name

    # first, save new alert
    r.hmset(key_map['alert_info'].format(alert_id=alert_id), description)

    # then log that alert record in our list of alerts
    r.zadd(key_map['alerts_historical'], now, alert_id)

    # then map this alert state name to the currently firing list of alerts
    r.hset(key_map['alert_currently_firing'], state_name, alert_id)

    return alert_id


def close_alert(r, state_name, alert_id):
    now = time.time()

    # first, take this alert out of our list of ongoing alerts
    r.hdel(key_map['alert_currently_firing'], state_name)

    alert_key = key_map['alert_info'].format(alert_id=alert_id)

    # then, update its status as closed
    r.hset(alert_key, 'end_time', now)

    # get start time
    start_time = r.hget(alert_key, 'start_time')

    if start_time:
        start_time = float(start_time)
    else:
        start_time = 0

    # record duration
    duration = now - start_time
    r.hset(alert_key, 'duration', duration)

    # send notifications
    notify_alert_closed(state_name, alert_id)


def should_send_ongoing_alert(last_ongoing_alert_email, alert_send_email_interval, alert_id):
    if not alert_send_email_interval or alert_send_email_interval == -1:
        return False

    now = int(time.time())

    if (now - last_ongoing_alert_email[alert_id]) > alert_send_email_interval:
        last_ongoing_alert_email[alert_id] = now
        return True

    return False


def main():
    configs = process_config()

    redis_url = configs.get('redis', 'localhost:6379')
    alert_process_interval = configs.get('alert_process_interval', default_alert_process_interval)
    server_staleness_duration = configs.get('server_staleness_duration', default_server_staleness_duration)
    alert_send_email_interval = configs.get('alert_send_email_interval', -1)

    r = redis.StrictRedis.from_url(redis_url)

    last_ongoing_alert_email = defaultdict(int)

    while True:
        logger.info('Starting alert run..')

        loop_start = time.time()
        closed_alerts = 0
        ongoing_alerts = 0
        new_alerts = 0

        # all currently bad alerts are here. dict of bad alert state name to info on that state
        bad_states = get_bad_states(r, server_staleness_duration)

        # 1: iterate through mapping of currently firing alerts in redis, checking if each
        # is stil in bad state. if not mark them as closed
        for state_name, alert_id in r.hgetall(key_map['alert_currently_firing']).iteritems():

            # Remove known alert from list of current states. It will then
            # be left with just new alerts.
            current_state = bad_states.pop(state_name, None)

            if current_state:
                logger.info('Alert "%s" still firing', state_name)
                if should_send_ongoing_alert(last_ongoing_alert_email, alert_send_email_interval, alert_id):
                    logger.info('Will send ongoing email')
                    notify_ongoing_alert(alert_id, state_name)
                else:
                    logger.info('Will not send ongoing email')
                ongoing_alerts += 1
            else:
                logger.info('Alert "%s" no longer firing. Closing.', state_name)
                closed_alerts += 1
                close_alert(r, state_name, alert_id)
                last_ongoing_alert_email.pop(alert_id, None)

        # 2: create new alerts for states which are bad but not yet kept track of
        for state_name, description in bad_states.iteritems():
            alert_id = create_alert(r, state_name, description)
            logger.info('Created new alert "%s" with id %s', state_name, alert_id)
            new_alerts += 1
            notify_alert_new(alert_id, state_name, description)

        # 3: purge records of ancient alerts
        # TODO

        # Log some info for this round
        loop_end = time.time()
        duration = loop_end - loop_start
        logger.info('New alerts: %s. Ongoing alerts: %s. Closed alerts: %s', new_alerts, ongoing_alerts, closed_alerts)
        logger.info('Alert processor ran in %.2f seconds. Will sleep %s seconds', duration, alert_process_interval)

        # Wait until next...
        time.sleep(alert_process_interval)


if __name__ == '__main__':
    main()
