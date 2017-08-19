# bits of code shared between agent/server/alerter

key_map = {
    # server info storage
    'server_last_posts': 'healthapp:server_last_posts',
    'server_info': 'healthapp:server_info:{server_name}',

    # alert storage

    # map state name to alert id
    'alert_currently_firing': 'healthapp:alerts_current',

    # info on alert
    'alert_info': 'healthapp:alert_info:{alert_id}',

    # historical list of alerts. purge this regularly.
    # sorted set with key being alert id and value being time
    'alerts_historical': 'healthapp:alerts_list'
}

default_server_staleness_duration = 4 * 60
default_alert_process_interval = 60
default_agent_run_interval = 60
