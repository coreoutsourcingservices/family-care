"""Purge expired recycle entries. Storage failures are retried without exposing data."""
import argparse
import time
import threading
from core.database import db
from services.recycle_bin import purge_one
_start_lock=threading.Lock()


def drain(app):
    with app.app_context():
        try:
            while purge_one():
                pass
        except Exception as exc:
            db().rollback()
            app.logger.warning('Recycle worker unavailable: %s',type(exc).__name__)


def start_background(app):
    with _start_lock:
        worker=app.extensions.get('recycle_worker')
        if worker and worker.is_alive():
            return
        def run():
            while True:
                drain(app)
                time.sleep(900)
        thread=threading.Thread(target=run,name='recycle-worker',daemon=True)
        app.extensions['recycle_worker']=thread
        thread.start()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    from app import create_app
    app=create_app()
    if args.once:
        drain(app)
    else:
        while True:
            drain(app)
            time.sleep(900)


if __name__=='__main__':
    main()
