"""Safe, read-only setup checks; never prints secrets/connection passwords.

Run: python scripts/diagnose.py
"""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    'flask': 'Flask', 'flask_cors': 'Flask-Cors', 'flask_limiter': 'Flask-Limiter',
    'sqlalchemy': 'SQLAlchemy', 'psycopg': 'psycopg', 'waitress': 'waitress',
    'alembic': 'alembic', 'jwt': 'PyJWT', 'argon2': 'argon2-cffi',
    'pydantic': 'pydantic', 'dotenv': 'python-dotenv', 'cloudinary': 'cloudinary',
    'pywebpush': 'pywebpush',
}


def main():
    print('FamilyCare local backend diagnostics (read-only)')
    print('Python:', sys.version.split()[0], 'at', sys.executable)
    missing = [display for module, display in PACKAGES.items() if importlib.util.find_spec(module) is None]
    if missing:
        print('[ERROR] Missing packages:', ', '.join(missing))
        print('  Fix: python -m pip install -r requirements.txt')
    else:
        print('[OK] Required Python modules importable')
    env_path = ROOT / '.env'
    if not env_path.exists():
        print('[ERROR] backend/.env absent (ZIP intentionally excludes private credentials)')
        print('  Fix: python scripts/configure_local.py')
        return 1
    try:
        from dotenv import dotenv_values
        env = dotenv_values(env_path)
    except ImportError:
        print('[ERROR] Install python-dotenv before checking .env')
        return 1
    for key in ('DATABASE_URL', 'JWT_SECRET_KEY', 'OTP_HMAC_SECRET'):
        val = env.get(key) or ''
        valid = bool(val) if key == 'DATABASE_URL' else len(val) >= 32
        print(('[OK]' if valid else '[ERROR]') + ' ' + key + (' configured' if valid else ' missing or too short'))
    if not (env.get('DATABASE_URL') or ''):
        print('  Configure Supabase PostgreSQL URL privately in backend/.env')
    if not missing and all(env.get(k) for k in ('DATABASE_URL', 'JWT_SECRET_KEY', 'OTP_HMAC_SECRET')):
        print('Next: python server.py --check  (tests database/schema connectivity)')
    else:
        print('Complete the checks above before starting the backend.')
    return int(bool(missing) or not all(env.get(k) for k in ('DATABASE_URL', 'JWT_SECRET_KEY', 'OTP_HMAC_SECRET')))


if __name__ == '__main__':
    raise SystemExit(main())
