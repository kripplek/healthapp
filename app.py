# Stateless web app
# Listen for requests from agents. Update their status in redis. Respond
# to general inquiries and host web ui.

import falcon
import redis
import hmac
import time
import ujson
import re
import os
from datetime import datetime

key_map = {
  'server_last_posts': 'healthapp:server_last_posts'
}

mimes = {'.css': 'text/css',
         '.jpg': 'image/jpeg',
         '.js': 'text/javascript',
         '.png': 'image/png',
         '.svg': 'image/svg+xml',
         '.ttf': 'application/octet-stream',
         '.woff': 'application/font-woff'}

ui_root = os.path.abspath(os.path.dirname(__file__))


_filename_ascii_strip_re = re.compile(r'[^A-Za-z0-9_.-]')


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
    def __init__(self, r):
        self.r = r

    def on_post(self, req, resp, server_name):
        now = int(time.time())
        self.r.zadd(key_map['server_last_posts'], now, server_name)


class ServerList:
    def __init__(self, r):
        self.r = r

    def on_get(self, req, resp):
        good_time = time.time() - (60 * 5)
        servers = self.r.zrevrange(key_map['server_last_posts'], 0, -1, withscores=True)
        pretty = ({
          'name': name,
          'time': str(datetime.fromtimestamp(date)),
          'good': date >= good_time
        } for name, date in servers)
        resp.body = ujson.dumps({'servers': pretty})


def get_app():
    r = redis.StrictRedis.from_url('localhost:6379')
    app = falcon.API()

    # Get updates from servers
    app.add_route('/api/v0/status/{server_name}', ServerStatus(r))

    # General listing of servers and their last status update
    app.add_route('/api/v0/servers', ServerList(r))

    # Pertaining to web UI
    app.add_route('/static/{filename}', StaticResource('/static'))
    app.add_sink(home_route, '/')

    return app
