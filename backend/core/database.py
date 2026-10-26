from flask import current_app, g
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import make_url


class Base(DeclarativeBase):
    metadata = MetaData(schema='familycare', naming_convention={
        'ix': 'ix_%(table_name)s_%(column_0_name)s', 'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s', 'pk': 'pk_%(table_name)s'})


def build_engine(url, config):
    if url.startswith(('postgres://', 'postgresql://')):
        url = 'postgresql+psycopg://' + url.split('://', 1)[1]
    if url.startswith('sqlite'):
        if not config.get('TESTING'):
            raise RuntimeError('SQLite is only allowed for isolated tests')
        return create_engine(url, poolclass=StaticPool, connect_args={'check_same_thread': False},
                             execution_options={'schema_translate_map': {'familycare': None}})
    parsed = make_url(url)
    if parsed.get_backend_name() != 'postgresql':
        raise RuntimeError('Supabase PostgreSQL DATABASE_URL required')
    ssl = parsed.query.get('sslmode', 'require')
    if ssl not in ('require', 'verify-ca', 'verify-full'):
        raise RuntimeError('PostgreSQL TLS required')
    return create_engine(url, pool_pre_ping=True, pool_recycle=300,
                         pool_size=config['DB_POOL_SIZE'], max_overflow=config['DB_MAX_OVERFLOW'],
                         pool_timeout=5, connect_args={'sslmode': ssl, 'connect_timeout': 5})


def init_database(app):
    app.extensions['database_engine'] = (build_engine(app.config['DATABASE_URL'], app.config)
                                          if app.config['DATABASE_URL'] else None)

    @app.teardown_appcontext
    def close_session(error=None):
        session = g.pop('db_session', None)
        if session:
            session.rollback()
            session.close()


def db():
    from core.errors import APIError
    engine = current_app.extensions['database_engine']
    if engine is None:
        raise APIError(503, 'database_not_configured', 'Configure DATABASE_URL and run migrations')
    if 'db_session' not in g:
        g.db_session = Session(engine, expire_on_commit=False)
    return g.db_session
