import smtplib
import logging
from config import process_config
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

message_templates = {
    'alert_new': {
        'subject': 'New Alert "%(state_name)s" !',
        'body': '''Hi,\n\nAlert "%(state_name)s" has just started firing.\n\n%(alert_id)s\n\nRegards'''
    },
    'alert_ongoing': {
        'subject': 'Alert "%(state_name)s" still firing',
        'body': '''Hi,\n\nAlert "%(state_name)s" is still firing after %(duration)s seconds.\n\n%(alert_id)s\n\nRegards'''
    },
    'alert_closed': {
        'subject': 'Alert "%(state_name)s" closed',
        'body': '''Hi,\n\nAlert "%(state_name)s" closed after %(duration)s seconds.\n\n%(alert_id)s\n\nRegards'''
    }
}


def notify_alert_new(alert_id, state_name, description):
    template = message_templates['alert_new']
    subject = template['subject'] % {'state_name': state_name}
    body = template['body'] % {'state_name': state_name, 'alert_id': alert_id, 'description': description, 'duration': ''}
    send_email(subject, body)


def notify_alert_closed(state_name, alert_id):
    template = message_templates['alert_closed']
    subject = template['subject'] % {'state_name': state_name}
    body = template['body'] % {'state_name': state_name, 'alert_id': alert_id, 'duration': ''}
    send_email(subject, body)


def notify_ongoing_alert(alert_id, state_name):
    template = message_templates['alert_ongoing']
    subject = template['subject'] % {'state_name': state_name}
    body = template['body'] % {'state_name': state_name, 'alert_id': alert_id, 'duration': ''}
    send_email(subject, body)


def send_email(subject, body):
    # value is memoized so we can call this more than once without issue
    configs = process_config()

    if not configs.get('enable_emails'):
        logger.debug('Alert emails disabled')
        return

    msg = MIMEText(body)

    msg['Subject'] = subject
    msg['From'] = configs['email_sender']
    msg['To'] = '; '.join(configs['email_recipients'])

    try:
        s = smtplib.SMTP(configs['email_server'])
        s.sendmail(configs['email_sender'], configs['email_recipients'], msg.as_string())
        s.quit()
    except Exception:
        logger.exception('Failed sending email')
