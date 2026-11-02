"""Local Windows Waitress launcher with visible startup and database diagnostics.

Run from backend/: python server.py [--check]
The Flask application factory for production remains in wsgi.py.
"""
import argparse
import os
import sys


def database_status(app):
    """Check the application schema without disclosing connection credentials."""
    engine = app.extensions.get('database_engine')
    if engine is None:
        return False, 'DATABASE_URL is missing in backend/.env'
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text('SELECT id FROM familycare.users LIMIT 0'))
        return True, 'PostgreSQL connection and familycare.users table OK'
    except Exception as exc:
        # Never print raw DB exceptions: they may include the username or DSN.
        name = type(exc).__name__
        return False, f'{name}: database unreachable, or migrations not applied'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Start or check the FamilyCare Flask backend')
    parser.add_argument('--check', action='store_true', help='Check app and DB, do not start server')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', '5001')))
    parser.add_argument('--no-push-worker', action='store_true', help='Disable optional doctor push worker for debugging')
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    try:
        from app import create_app
        app = create_app()
    except (ImportError, ModuleNotFoundError) as exc:
        print(f'[ERROR] Missing Python dependency: {exc}', file=sys.stderr, flush=True)
        print('Install packages: python -m pip install -r requirements.txt', file=sys.stderr)
        return 1
    except Exception as exc:
        message = str(exc) if isinstance(exc, RuntimeError) and '://' not in str(exc) else type(exc).__name__
        print(f'[ERROR] Flask initialization failed: {message}', file=sys.stderr, flush=True)
        print('Run: python scripts/configure_local.py and check backend/.env', file=sys.stderr)
        return 1

    ready, detail = database_status(app)
    print('[FamilyCare] Flask app initialized.', flush=True)
    print(f'[FamilyCare] Database: {detail}', flush=True)
    if not ready:
        print('[FamilyCare] Accounts/dashboard require PostgreSQL and latest migrations.', flush=True)
        print('[FamilyCare] Check backend/.env then run: python -m alembic upgrade head', flush=True)
    if args.check:
        return 0 if ready else 1

    try:
        from waitress import serve
    except ImportError:
        print('[ERROR] Install Waitress: python -m pip install -r requirements.txt', file=sys.stderr)
        return 1
    if not args.no_push_worker and ready:
        from doctor.push_worker import start
        start(app)
    if ready and args.port == 5001:
        from scripts.report_worker import start_background as start_reports
        start_reports(app)
        from scripts.notification_socket import start_background
        start_background(app)
    print(f'[FamilyCare] Starting at http://127.0.0.1:{args.port}', flush=True)
    print(f'[FamilyCare] Health: http://127.0.0.1:{args.port}/api/v1/health', flush=True)
    print('[FamilyCare] This terminal stays occupied while the server runs. Press Ctrl+C to stop.', flush=True)
    try:
        serve(app, host='127.0.0.1', port=args.port, threads=8)
    except OSError:
        print(f'[ERROR] Could not bind port {args.port}. Is another backend already running?', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\n[FamilyCare] Server stopped.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
