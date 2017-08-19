# bits of code shared between agent/server/alerter

key_map = {
    # server info storage
    'server_last_posts': 'healthapp:server_last_posts',
    'server_auth_key': 'healthapp:server_key:{server_name}',
    'server_info': 'healthapp:server_info:{server_name}',

    # alert storage

    # map state name to alert id
    'alert_currently_firing': 'healthapp:alerts_current',

    # alert id
    'alert_info': 'healthapp:alert_info:{alert_id}',

    # historical list of alerts. purge this regularly.
    # sorted set with key being alert id and value being time
    'alerts_historical': 'healthapp:alerts_list'
}

server_staleness_interal = 5 * 60

alert_process_interval = 60

agent_run_interval = 60

email_recipient = 'Joe G <joe@joegillotti.com>'
email_sender = 'Healthapp <noreply@gshost.us>'
email_server = ''
