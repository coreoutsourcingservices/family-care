"""Local appointment-only outbox worker; general mail_worker also supports these emails."""
import os
import threading
from services.email import process_one


def start_background(app):
    if not os.getenv('SMTP_HOST') or not os.getenv('SMTP_FROM'):
        app.logger.warning('Appointment emails remain queued: SMTP_HOST and SMTP_FROM are required')
        return
    if app.extensions.get('appointment_mail_worker'):
        return
    def run():
        stop = threading.Event()
        while not stop.is_set():
            with app.app_context():
                try:
                    worked = process_one(templates=['appointment_booked'])
                except Exception as exc:
                    app.logger.warning('Appointment email worker: %s', type(exc).__name__)
                    worked = False
            if not worked:
                stop.wait(2)
    thread = threading.Thread(target=run, name='appointment-mail', daemon=True)
    app.extensions['appointment_mail_worker'] = thread
    thread.start()
