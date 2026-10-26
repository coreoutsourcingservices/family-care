import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def settings(overrides=None):
    load_dotenv(ROOT / '.env')
    config = dict(APP_ENV=os.getenv('APP_ENV', 'development'),
                  DATABASE_URL=os.getenv('DATABASE_URL', ''),
                  JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', ''),
                  OTP_HMAC_SECRET=os.getenv('OTP_HMAC_SECRET', ''),
                  JWT_ISSUER=os.getenv('JWT_ISSUER', 'familycare-api'),
                  JWT_AUDIENCE=os.getenv('JWT_AUDIENCE', 'familycare-clients'),
                  ACCESS_TOKEN_MINUTES=int(os.getenv('ACCESS_TOKEN_MINUTES', '15')),
                  REFRESH_TOKEN_DAYS=int(os.getenv('REFRESH_TOKEN_DAYS', '7')),
                  DB_POOL_SIZE=int(os.getenv('DB_POOL_SIZE', '5')),
                  DB_MAX_OVERFLOW=int(os.getenv('DB_MAX_OVERFLOW', '2')),
                  RATELIMIT_STORAGE_URI=os.getenv('RATELIMIT_STORAGE_URI', 'memory://'),
                  COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
                  CORS_ORIGINS=[v.strip() for v in os.getenv('CORS_ORIGINS', '').split(',') if v.strip()],
                  MAX_CONTENT_LENGTH=16384, TESTING=False)
    config.update(overrides or {})
    for key in ('JWT_SECRET_KEY', 'OTP_HMAC_SECRET'):
        if len(config[key]) < 32:
            raise RuntimeError(f'{key} requires 32+ random characters; run scripts/configure_local.py')
    if config['JWT_SECRET_KEY'] == config['OTP_HMAC_SECRET']:
        raise RuntimeError('JWT and OTP secrets must differ')
    if config['APP_ENV'] == 'production':
        if not config['COOKIE_SECURE'] or not config['RATELIMIT_STORAGE_URI'].startswith(('redis://', 'rediss://')):
            raise RuntimeError('Production requires secure cookies and Redis rate limiting')
    return config
