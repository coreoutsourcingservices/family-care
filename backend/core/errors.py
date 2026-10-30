from flask import jsonify, current_app
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, OperationalError
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def register_errors(app):
    @app.errorhandler(APIError)
    def api_error(error):
        return jsonify(error={'code': error.code, 'message': error.message}), error.status

    @app.errorhandler(ValidationError)
    def invalid_input(error):
        fields = [{'field': '.'.join(map(str, e['loc'])), 'type': e['type'], 'message':e['msg']}
                  for e in error.errors(include_input=False, include_context=False)]
        return jsonify(error={'code': 'validation_error', 'message': 'Invalid request fields', 'fields': fields}), 422

    @app.errorhandler(IntegrityError)
    def conflict(error):
        return jsonify(error={'code': 'conflict', 'message': 'Account or registration details already exist'}), 409

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        current_app.logger.warning('Database operation failed: %s', type(error).__name__)
        if isinstance(error,OperationalError):
            return jsonify(error={'code':'database_unavailable','message':'Database connection is temporarily unavailable. Please retry shortly.'}),503
        return jsonify(error={'code': 'database_unavailable', 'message': 'Database unavailable or schema not installed'}), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error={'code': error.name.lower().replace(' ', '_'), 'message': error.description}), error.code

    @app.errorhandler(Exception)
    def unexpected(error):
        current_app.logger.error('Unhandled backend error: %s', type(error).__name__)
        return jsonify(error={'code': 'internal_error', 'message': 'Unexpected server error'}), 500
