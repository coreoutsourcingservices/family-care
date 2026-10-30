import time
from threading import Thread


def run(app, once=False):
    from doctor.notifications import deliver_pending
    while True:
        try:
            with app.app_context():
                deliver_pending()
        except Exception:
            app.logger.warning('Doctor push worker deferred a delivery batch')
        if once:
            return
        time.sleep(15)


def start(app):
    worker = Thread(target=run, args=(app,), name='doctor-web-push', daemon=True)
    worker.start()
    return worker
