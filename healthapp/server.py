# Stateless web app
# Listen for requests from agents. Update their status in redis. Respond
# to general inquiries and host web ui.

import falcon
import redis
import time
import ujson
import re
import os
import hashlib
import base64
import hmac
from datetime import datetime, timedelta
from operator import itemgetter

from constants import key_map, default_server_staleness_duration
from config import process_config

mimes = {'.css': 'text/css',
         '.jpg': 'image/jpeg',
         '.js': 'text/javascript',
         '.png': 'image/png',
         '.svg': 'image/svg+xml',
         '.ttf': 'application/octet-stream',
         '.woff': 'application/font-woff'}

ui_root = os.path.abspath(os.path.dirname(__file__))

_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')


def confirm_hmac(r, server_name, body, api_key, given_hmac):
    hmac_obj = hmac.new(api_key, body, hashlib.sha512)
    return hmac.compare_digest(hmac_obj.digest(), given_hmac)


def get_server_info(r, server_name):
    info = r.get(key_map['server_info'].format(server_name=server_name))
    if not info:
        return {}

    try:
        data = ujson.loads(info)
    except ValueError:
        return {}

    data['name'] = server_name

    last_updated = r.zscore(key_map['server_last_posts'], server_name)

    if last_updated:
        data['Last Updated'] = str(datetime.fromtimestamp(last_updated))

    return data


def get_alert_info(r, alert_id):
    info = r.hgetall(key_map['alert_info'].format(alert_id=alert_id))
    if not info:
        return {}

    state_name = info.get('state_name')

    if not state_name:
        return {}

    start_time = int(float(info['start_time']))
    end_time = int(float(info['end_time']))

    info['ongoing'] = end_time == -1

    if end_time == -1:
        end_time = int(time.time())
        info['end_time'] = 'Ongoing'
    else:
        info['end_time'] = str(datetime.fromtimestamp(end_time))

    info['duration'] = str(timedelta(seconds=end_time - start_time))
    info['alert_id'] = alert_id
    info['start_time'] = str(datetime.fromtimestamp(start_time))

    alert_parts = state_name.split('_', 1)

    if alert_parts[0] == 'stale':
        info['human_bad'] = 'Offline'

    info['server'] = get_server_info(r, alert_parts[1])

    # server record missing. possible if you've manually deleted records
    if not info['server']:
        info['server'] = {'name': alert_parts[1], 'OS': 'Linux'}

    return info


class StaticResource(object):
    def __init__(self, path):
        self.path = path.lstrip('/')

    def on_get(self, req, resp, filename):
        suffix = os.path.splitext(req.path)[1]
        resp.content_type = mimes.get(suffix, 'application/octet-stream')

        filepath = os.path.join(ui_root, self.path, secure_filename(filename))
        try:
            resp.stream = open(filepath, 'rb')
            resp.stream_len = os.path.getsize(filepath)
        except IOError:
            raise falcon.HTTPNotFound()


def secure_filename(filename):
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, ' ')
    filename = str(_filename_ascii_strip_re.sub('', '_'.join(
        filename.split()))).strip('._')
    return filename


def home_route(req, resp):
    resp.content_type = 'text/html'
    resp.body = open(os.path.join(ui_root, 'static/spa.html')).read()


class ServerStatus:
    def __init__(self, r, api_key):
        self.r = r
        self.api_key = api_key

    def on_post(self, req, resp, server_name):
        hmac_header = req.get_header('X-INTEGRITY')

        if not hmac_header:
            raise falcon.HTTPUnauthorized('Missing hmac token')

        hmac_digest = base64.urlsafe_b64decode(hmac_header)

        raw_body = req.stream.read()

        if not confirm_hmac(self.r, server_name, raw_body, self.api_key, hmac_digest):
            raise falcon.HTTPUnauthorized('Incorrect hmac')

        try:
            ujson.loads(raw_body)
        except ValueError:
            raise falcon.HTTPBadRequest('Failed parsing json body')

        self.r.set(key_map['server_info'].format(server_name=server_name), raw_body)

        now = int(time.time())
        self.r.zadd(key_map['server_last_posts'], now, server_name)

    def on_get(self, req, resp, server_name):
        info = get_server_info(self.r, server_name)

        if not info:
            raise falcon.HTTPNotFound()

        resp.body = ujson.dumps(info)


class ServerList:
    def __init__(self, r, server_staleness_duration):
        self.r = r
        self.server_staleness_duration = server_staleness_duration

    def on_get(self, req, resp):
        good_time = time.time() - self.server_staleness_duration
        servers = self.r.zrange(key_map['server_last_posts'], 0, -1, withscores=True)
        pretty = ({
            'name': name,
            'time': str(datetime.fromtimestamp(date)),
            'good': date >= good_time,
            'info': get_server_info(self.r, name)
        } for name, date in servers)
        resp.body = ujson.dumps({'servers': sorted(pretty, key=itemgetter('name'))})


class AlertList:
    def __init__(self, r):
        self.r = r

    def on_get(self, req, resp):
        active_ids = set()
        active_alerts = []

        for state_name, alert_id in self.r.hgetall(key_map['alert_currently_firing']).iteritems():
            active_alerts.append(get_alert_info(self.r, alert_id))
            active_ids.add(alert_id)

        historical_alerts = []

        for alert_id in self.r.zrevrange(key_map['alerts_historical'], 0, -1):
            if alert_id not in active_ids:
                info = get_alert_info(self.r, alert_id)
                if info:
                    historical_alerts.append(info)

        resp.body = ujson.dumps({'active': active_alerts, 'historical': historical_alerts})


class Alert:
    def __init__(self, r):
        self.r = r

    def on_get(self, req, resp, alert_id):
        info = get_alert_info(self.r, alert_id)

        if not info:
            raise falcon.HTTPNotFound()

        resp.body = ujson.dumps(info)


def get_app():
    configs = process_config()

    redis_url = configs.get('redis', 'localhost:6379')
    server_staleness_duration = configs.get('server_staleness_duration', default_server_staleness_duration)
    api_key = configs.get('api_key')

    r = redis.StrictRedis.from_url(redis_url)

    app = falcon.API()

    # Get updates from servers
    app.add_route('/api/v0/status/{server_name}', ServerStatus(r, api_key))

    # General listing of servers and their last status update
    app.add_route('/api/v0/servers', ServerList(r, server_staleness_duration))

    # List alerts. All active + 50 historical.
    app.add_route('/api/v0/alerts', AlertList(r))
    app.add_route('/api/v0/alert/{alert_id}', Alert(r))

    # Pertaining to web UI
    app.add_route('/static/{filename}', StaticResource('/static'))
    app.add_sink(home_route, '/')

    return app
