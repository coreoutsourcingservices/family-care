import os
from pathlib import Path
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from app import create_app
from core.database import Base
from core.models import User, uid
from core.security import password_hasher


@pytest.fixture(scope='session')
def test_app():
    url = os.getenv('TEST_DATABASE_URL', 'sqlite://')
    if url != 'sqlite://':
        from sqlalchemy.engine import make_url
        parsed = make_url(url)
        if parsed.host not in ('127.0.0.1', 'localhost') or not (parsed.database or '').endswith('_test'):
            raise RuntimeError('Tests only accept a loopback database ending in _test; schema is recreated')
    app = create_app(dict(TESTING=True, APP_ENV='development', DATABASE_URL=url,
                          JWT_SECRET_KEY='test-jwt-key-'+'a'*48, OTP_HMAC_SECRET='test-otp-key-'+'b'*48,
                          RATELIMIT_ENABLED=False, COOKIE_SECURE=False,
                          RATELIMIT_STORAGE_URI='memory://', CORS_ORIGINS=['http://localhost:3000']))
    engine = app.extensions['database_engine']
    if engine.dialect.name == 'postgresql':
        with engine.begin() as connection:
            connection.exec_driver_sql('DROP SCHEMA IF EXISTS familycare CASCADE')
            cursor = connection.connection.driver_connection.cursor()
            cursor.execute(Path('supabase/0001_identity.sql').read_text(), prepare=False)
            cursor.close()
            from alembic.migration import MigrationContext
            from alembic.operations import Operations
            import importlib
            with Operations.context(MigrationContext.configure(connection)):
                importlib.import_module('migrations.versions.0003_doctor_referrals').upgrade()
                importlib.import_module('migrations.versions.0004_members_and_cloudinary').upgrade()
                importlib.import_module('migrations.versions.0005_care_profile_public_ids').upgrade()
                importlib.import_module('migrations.versions.0006_child_records').upgrade()
                importlib.import_module('migrations.versions.0007_vaccination_management').upgrade()
                importlib.import_module('migrations.versions.0008_report_text').upgrade()
                importlib.import_module('migrations.versions.0010_optional_doctor_degree').upgrade()
                importlib.import_module('migrations.versions.0011_doctor_onboarding').upgrade()
                importlib.import_module('migrations.versions.0012_doctor_verification_check').upgrade()
                importlib.import_module('migrations.versions.0013_doctor_onboarding_images').upgrade()
                importlib.import_module('migrations.versions.0014_doctor_notifications').upgrade()
                importlib.import_module('migrations.versions.0015_adult_records').upgrade()
                importlib.import_module('migrations.versions.0016_child_profile_controls').upgrade()
                importlib.import_module('migrations.versions.0017_realtime_notifications').upgrade()
    else:
        Base.metadata.create_all(engine)
    yield app
    engine.dispose()


@pytest.fixture
def app(test_app):
    test_app.extensions['pending_signups'].items.clear()
    engine = test_app.extensions['database_engine']
    with engine.begin() as connection:
        if engine.dialect.name == 'postgresql':
            connection.exec_driver_sql('TRUNCATE familycare.users, familycare.vaccines CASCADE')
        else:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


def create_account(app, role='SUPERADMIN', email=None, change=False):
    from core.database import db
    account_id = uid()
    with app.app_context():
        account = User(id=account_id, public_id='superadmin' if role == 'SUPERADMIN' else None,
                       username='superadmin' if role == 'SUPERADMIN' else None,
                       full_name='Test User', email=email or f'{account_id}@example.com',
                       password_hash=password_hasher.hash('Password8!'), role=role,
                       email_verified=True, approval_status='APPROVED', must_change_password=change)
        if db().bind.dialect.name == 'sqlite' and role != 'SUPERADMIN':
            account.public_id = role[0] + account_id
        db().add(account)
        db().commit()
    return account_id


@pytest.fixture(autouse=True)
def mock_signup_mail():
    from unittest.mock import patch
    with patch('services.signup.send_mail') as sender:
        yield sender
