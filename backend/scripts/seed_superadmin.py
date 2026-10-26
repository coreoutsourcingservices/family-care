"""Run from backend: python -m scripts.seed_superadmin."""
import os
import getpass
from sqlalchemy import select, text
from app import create_app
from core.database import db
from core.models import User, uid
from core.security import password_hasher
from core.schemas import ForgotPassword
from core.errors import APIError


def seed(username, email, password):
    if username != 'superadmin':
        raise ValueError('Bootstrap username must be superadmin')
    from flask import current_app
    if len(password) < 8 or len(password) > 128:
        raise ValueError('Password must be 8-128 characters')
    if current_app.config['APP_ENV'] == 'production' and password == 'superadmin@2026':
        raise ValueError('Default bootstrap password is prohibited in production')
    email = str(ForgotPassword(email=email).email).lower()
    if db().bind.dialect.name == 'postgresql':
        db().execute(text('SELECT pg_advisory_xact_lock(812365)'))
    existing = db().scalar(select(User).where(User.username == username))
    if existing:
        if existing.role != 'SUPERADMIN':
            raise ValueError('Username belongs to another role')
        return existing, False
    account = User(id=uid(), public_id='superadmin', username=username, full_name='Super Admin',
                   email=email, password_hash=password_hasher.hash(password), role='SUPERADMIN',
                   email_verified=True, approval_status='APPROVED', account_status='ACTIVE',
                   must_change_password=True)
    db().add(account)
    db().commit()
    return account, True


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        email = os.getenv('SUPERADMIN_EMAIL') or input('Super admin email: ').strip()
        password = os.getenv('SUPERADMIN_PASSWORD') or getpass.getpass('Initial password: ')
        try:
            account, created = seed(os.getenv('SUPERADMIN_USERNAME', 'superadmin'), email, password)
            print('Super admin created; change password on first login.' if created else 'Already exists; unchanged.')
        except (APIError, ValueError) as error:
            print(getattr(error, 'message', str(error)))
            raise SystemExit(1)
