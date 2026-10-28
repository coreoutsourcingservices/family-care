import argparse
import time
from app import create_app
from services.email import process_one


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    app = create_app()
    last_vaccination_scan=0
    while True:
        with app.app_context():
            try:
                if time.monotonic()-last_vaccination_scan>=60:
                    from services.vaccination import queue_reminder_emails
                    queue_reminder_emails()
                    last_vaccination_scan=time.monotonic()
            except Exception as error:
                from core.database import db
                db().rollback()
                app.logger.warning('Vaccination reminder scan unavailable: %s', type(error).__name__)
                last_vaccination_scan=time.monotonic()
            try:
                worked = process_one()
            except Exception as error:
                app.logger.warning('Mail worker unavailable: %s', type(error).__name__)
                worked = False
        if args.once:
            break
        if not worked:
            time.sleep(2)


if __name__ == '__main__':
    main()
