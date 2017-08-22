import click
import redis

from constants import key_map
from config import process_config


def load_redis():
    configs = process_config()
    redis_url = configs.get('redis', 'localhost:6379')
    return redis.StrictRedis.from_url(redis_url)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--server', help='Server to forget', required=True)
def forget(server):
    server_name = server

    r = load_redis()

    for alert_id in r.zrange(key_map['server_alerts'].format(server_name=server_name), 0, -1, withscores=False):
        r.zrem(key_map['alerts_historical'], alert_id)
        r.delete(key_map['alert_info'].format(alert_id=alert_id))

    r.delete(key_map['server_alerts'].format(server_name=server_name))

    r.zrem(key_map['server_last_posts'], server_name)

    r.delete(key_map['server_info'].format(server_name=server_name))


def main():
    cli()
