import falcon
import redis
import hmac
import time
import ujson
from datetime import datetime

key_map = {
  'server_last_posts': 'healthapp:server_last_posts'
}


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
        servers = self.r.zrevrange(key_map['server_last_posts'], 0, -1, withscores=True)
        pretty = ((name, str(datetime.fromtimestamp(date))) for name, date in servers)
        resp.body = ujson.dumps(pretty)


def get_app():
    r = redis.StrictRedis.from_url('localhost:6379')
    app = falcon.API()

    app.add_route('/api/v0/status/{server_name}', ServerStatus(r))
    app.add_route('/api/v0/servers', ServerList(r))

    return app
