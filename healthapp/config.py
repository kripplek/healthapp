import os
import yaml
import ujson
import logging

logger = logging.getLogger()

saved_configs = None


def process_config():

    # let this be called more than once from anywhere without
    # reparsing the config files
    if saved_configs:
        return saved_configs

    config_files = [
        os.environ.get('CONFIG_FILE'),
        '/etc/healthapp/config.yaml',
        '/usr/local/healthapp/config.yaml',
        'config.yaml'
    ]

    configs = None

    for path in config_files:
        if not path:
            continue

        if os.path.exists(path):
            logger.info('Loading config from %s..', path)
            with open(path) as h:
                if path.endswith('.json'):
                    configs = ujson.load(h)
                    break
                elif path.endswith('.yaml'):
                    configs = yaml.load(h)
                    break
                else:
                    logger.error('unknown filetype %s', path)

    if not configs:
        logger.error('failed loading configs')
        return {}

    global saved_configs
    saved_configs = configs

    return saved_configs
