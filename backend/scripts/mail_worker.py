import argparse
import time
from app import create_app
from services.email import process_one


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    app = create_app()
    while True:
        with app.app_context():
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
