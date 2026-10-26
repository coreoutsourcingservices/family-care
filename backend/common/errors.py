import requests
from flask import jsonify
from werkzeug.exceptions import HTTPException
from common.supabase import UpstreamError

def register_errors(app):
    @app.errorhandler(UpstreamError)
    def upstream_error(error):
        status = error.status
        if status == 503:
            return jsonify(error='Configure Supabase in backend/.env'), 503
        if status == 429:
            return jsonify(error='Too many requests; try again later'), 429
        if status >= 500:
            return jsonify(error='Authentication service unavailable'), 502
        if status in (401, 403):
            return jsonify(error='Authentication failed or access denied'), 401
        return jsonify(error='Request rejected; check credentials, email confirmation and input'), 400

    @app.errorhandler(requests.RequestException)
    def network_error(error):
        return jsonify(error='Cannot reach Supabase; try again later'), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

