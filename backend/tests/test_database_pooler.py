from unittest.mock import patch
from flask import Flask
from sqlalchemy.exc import OperationalError
from core.database import build_engine
from core.errors import register_errors

def test_transaction_pooler_disables_named_prepared_statements():
    with patch('core.database.create_engine') as create:
        build_engine('postgresql://example:placeholder@pooler.example.org:6543/postgres',{'DB_POOL_SIZE':2,'DB_MAX_OVERFLOW':0})
        assert create.call_args.kwargs['connect_args']['prepare_threshold'] is None
        assert create.call_args.kwargs['pool_pre_ping'] is True

def test_session_pooler_keeps_default_driver_settings():
    with patch('core.database.create_engine') as create:
        build_engine('postgresql://example:placeholder@pooler.example.org:5432/postgres',{'DB_POOL_SIZE':2,'DB_MAX_OVERFLOW':0})
        assert 'prepare_threshold' not in create.call_args.kwargs['connect_args']

def test_connection_failure_is_not_reported_as_missing_schema():
    app=Flask(__name__);register_errors(app)
    @app.get('/failure')
    def failure():raise OperationalError('select 1',{},Exception('MaxClientsInSessionMode'))
    response=app.test_client().get('/failure')
    assert response.status_code==503
    assert response.json['error']['code']=='database_unavailable'
    assert 'connection' in response.json['error']['message'].lower()
    assert 'schema' not in response.json['error']['message'].lower()
