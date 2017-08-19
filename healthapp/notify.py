import smtplib
import logging
import constants
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
    send_email(constants.email_server, constants.email_recipient, subject, body)


def notify_alert_closed(state_name, alert_id):
    template = message_templates['alert_closed']
    subject = template['subject'] % {'state_name': state_name}
    body = template['body'] % {'state_name': state_name, 'alert_id': alert_id, 'duration': ''}
    send_email(constants.email_server, constants.email_recipient, subject, body)


def notify_ongoing_alert(alert_id, state_name):
    template = message_templates['alert_ongoing']
    subject = template['subject'] % {'state_name': state_name}
    body = template['body'] % {'state_name': state_name, 'alert_id': alert_id, 'duration': ''}
    send_email(constants.email_server, constants.email_recipient, subject, body)


def send_email(email_server, recipient, subject, body):
    return
    msg = MIMEText(body)

    msg['Subject'] = subject
    msg['From'] = 'HealthApp <noreply@gshost.us>'
    msg['To'] = recipient

    try:
        s = smtplib.SMTP(constants.email_server)
        s.sendmail(constants.email_sender, [recipient], msg.as_string())
        s.quit()
    except Exception:
        logger.exception('Failed sending email')
