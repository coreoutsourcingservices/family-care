from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import timedelta
import pytest
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from core.models import User, OTPChallenge, uid, now
from core.database import db
from services.otp import otp_code
from core.security import decode_token
from test_workflows import registration, verify, bearer, super_login


@pytest.fixture
def pg(app):
    engine = app.extensions['database_engine']
    if engine.dialect.name != 'postgresql':
        pytest.skip('Set isolated loopback TEST_DATABASE_URL ending in _test to exercise PostgreSQL locks/sequences')
    return engine


@pytest.mark.postgres
def test_concurrent_database_ids_no_duplicates_or_reuse(pg):
    def insert(index):
        with Session(pg) as session:
            user = User(id=uid(), public_id=None, full_name='Concurrency test', email=f'concurrent{index}@example.com',
                        password_hash='not-a-real-login-hash', role=('ADMIN','DOCTOR','PATIENT')[index % 3])
            session.add(user); session.flush(); session.refresh(user)
            value = user.public_id
            session.commit()
            return value
    with ThreadPoolExecutor(max_workers=12) as executor:
        ids = list(executor.map(insert, range(100)))
    assert len(set(ids)) == 100
    assert all(value[0] in 'ADC' and value[1:].isdigit() for value in ids)
    with pg.begin() as connection:
        connection.execute(text('DELETE FROM familycare.users'))
    assert insert(101) not in ids


@pytest.mark.postgres
def test_id_overflow_and_immutability(pg):
    with pg.begin() as connection:
        connection.execute(text("SELECT setval('familycare.patient_id_seq', 999999, true)"))
    with Session(pg) as session:
        user = User(id=uid(), full_name='Overflow', email='overflow@example.com', role='PATIENT', password_hash='test')
        session.add(user); session.flush(); session.refresh(user)
        assert user.public_id == 'C1000000'
        user.public_id = 'C000001'
        with pytest.raises(Exception):
            session.commit()
        session.rollback()


@pytest.mark.postgres
def test_concurrent_otp_only_one_session(app, client, pg):
    registered = client.post('/api/v1/patients/register', json=registration())
    with app.app_context():
        cid = decode_token(registered.json['challenge_token'], 'challenge')['cid']
        value = otp_code(cid)
    def verify_once(_):
        with app.test_client() as local:
            return local.post('/api/v1/patients/verify-email', json={
                'challenge_token': registered.json['challenge_token'], 'otp': value}).status_code
    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(verify_once, range(8)))
    assert statuses.count(200) == 1
    assert statuses.count(400) == 7


@pytest.mark.postgres
def test_concurrent_refresh_reuse_revokes_family(app, client, pg):
    session = super_login(app, client)
    def refresh_once(_):
        with app.test_client() as local:
            response = local.post('/api/v1/auth/refresh', json={'refresh_token': session.json['refresh_token']})
            return response.status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(refresh_once, range(2)))
    assert sorted(statuses) == [200, 401]
    assert client.get('/api/v1/superadmin/me', headers=bearer(session)).status_code == 401


@pytest.mark.postgres
def test_private_schema_denies_unprivileged_role(pg):
    from sqlalchemy.exc import DBAPIError
    with pg.connect() as connection:
        tx = connection.begin()
        connection.exec_driver_sql('CREATE ROLE familycare_probe NOLOGIN')
        connection.exec_driver_sql('SET LOCAL ROLE familycare_probe')
        with pytest.raises(DBAPIError):
            connection.exec_driver_sql('SELECT id FROM familycare.users LIMIT 0')
        tx.rollback()  # Also removes the temporary database role.


@pytest.mark.postgres
def test_models_and_sql_schema_match(pg):
    from alembic.migration import MigrationContext
    from alembic.autogenerate import compare_metadata
    from core.database import Base
    with pg.connect() as connection:
        context = MigrationContext.configure(connection, opts={'include_schemas': True})
        assert compare_metadata(context, Base.metadata) == []
