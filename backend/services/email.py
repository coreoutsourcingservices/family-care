import json
import os
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage
from flask import render_template
from sqlalchemy import select
from core.database import db
from core.models import EmailNotification, OTPChallenge, User, now
from services.otp import otp_code


def send_mail(destination, subject, body, message_id):
    host, sender = os.getenv('SMTP_HOST'), os.getenv('SMTP_FROM')
    if not host or not sender:
        raise RuntimeError('SMTP_HOST and SMTP_FROM required')
    use_ssl = os.getenv('SMTP_SSL', 'false').lower() == 'true'
    starttls = os.getenv('SMTP_STARTTLS', 'true').lower() == 'true'
    if not use_ssl and not starttls and os.getenv('SMTP_ALLOW_INSECURE', 'false').lower() != 'true':
        raise RuntimeError('SMTP TLS required; insecure mode only for a local mail sink')
    message = EmailMessage()
    message['From'], message['To'], message['Subject'] = sender, destination, subject
    message['Message-ID'] = f'<{message_id}@familycare.local>'
    message.set_content(body)
    cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    kwargs = {'context': ssl.create_default_context()} if use_ssl else {}
    with cls(host, int(os.getenv('SMTP_PORT', '587')), timeout=15, **kwargs) as client:
        if starttls and not use_ssl:
            client.starttls(context=ssl.create_default_context())
        if os.getenv('SMTP_USERNAME'):
            client.login(os.environ['SMTP_USERNAME'], os.environ.get('SMTP_PASSWORD', ''))
        client.send_message(message)


def process_one():
    # Lock stays held through delivery; bound worker count limits DB connections.
    # SMTP provides at-least-once delivery: crash after send/before commit may duplicate.
    item = db().scalar(select(EmailNotification).where(EmailNotification.status == 'PENDING',
                 EmailNotification.available_at <= now()).order_by(EmailNotification.created_at)
                 .with_for_update(skip_locked=True).limit(1))
    if not item:
        db().rollback()
        return False
    user = db().get(User, item.user_id)
    if item.template.startswith('vaccination_reminder_'):
        from services.vaccination import reminder_still_valid
        if not reminder_still_valid(item):
            item.status = 'CANCELLED'
            db().commit()
            return True
    context = json.loads(item.context_json)
    if item.challenge_id:
        challenge = db().get(OTPChallenge, item.challenge_id)
        if challenge.consumed_at or challenge.expires_at <= now():
            item.status = 'CANCELLED'
            db().commit()
            return True
        context['otp'] = otp_code(challenge.id)
    body = render_template('emails/' + item.template + '.txt', full_name=user.full_name, **context)
    try:
        send_mail(user.email, 'Family Care - ' + item.template.replace('_', ' '), body, item.id)
        item.status, item.sent_at = 'SENT', now()
    except (OSError, smtplib.SMTPException, RuntimeError):
        item.attempts += 1
        item.status = 'FAILED' if item.attempts >= 8 else 'PENDING'
        item.available_at = now() + timedelta(seconds=min(300, 2**item.attempts * 5))
    db().commit()
    return True
