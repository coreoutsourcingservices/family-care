import os
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

load_dotenv()


class UpstreamError(Exception):
    def __init__(self, status):
        self.status = status


def create_app():
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=16384)

    def supabase(method, path, token=None, **kwargs):
        url = os.getenv('SUPABASE_URL', '').rstrip('/')
        key = os.getenv('SUPABASE_ANON_KEY', '')
        if not url or not key or 'your-project' in url:
            raise UpstreamError(503)
        headers = {'apikey': key, 'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        response = requests.request(method, url + path, headers=headers, timeout=15, **kwargs)
        if not response.ok:
            raise UpstreamError(response.status_code)
        return response.json() if response.content else {}

    def protected(*roles):
        def decorate(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                header = request.headers.get('Authorization', '')
                if not header.startswith('Bearer ') or not header[7:].strip():
                    return jsonify(error='Bearer access token required'), 401
                g.token = header[7:].strip()
                g.user = supabase('GET', '/auth/v1/user', g.token)
                profiles = supabase('GET', '/rest/v1/profiles', g.token,
                                     params={'id': f'eq.{g.user["id"]}', 'select': 'id,full_name,role'})
                if not profiles:
                    return jsonify(error='Profile unavailable; contact administrator'), 403
                g.profile = profiles[0]
                if roles and g.profile['role'] not in roles:
                    return jsonify(error='Insufficient permissions'), 403
                return fn(*args, **kwargs)
            return wrapped
        return decorate

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

    def body():
        data = request.get_json()
        if not isinstance(data, dict):
            return None
        return data

    @app.get('/health')
    def health():
        return jsonify(status='ok', service='familycare-backend')

    @app.post('/api/auth/signup')
    def signup():
        data = body()
        if data is None:
            return jsonify(error='JSON object required'), 400
        email, password = data.get('email'), data.get('password')
        name, role = data.get('full_name'), data.get('role', 'patient')
        if role not in ('patient', 'doctor'):
            return jsonify(error='Public signup allows patient or doctor only'), 400
        if (not isinstance(email, str) or '@' not in email or len(email) > 254
                or not isinstance(password, str) or not 12 <= len(password) <= 128
                or not isinstance(name, str) or not 1 <= len(name.strip()) <= 120):
            return jsonify(error='Valid email, full_name and password (12–128 characters) required'), 400
        result = supabase('POST', '/auth/v1/signup', json={
            'email': email.strip(), 'password': password,
            'data': {'full_name': name.strip(), 'role': role}})
        return jsonify(message='Signup submitted. Check your email to confirm your account.',
                       user_id=result.get('id') or result.get('user', {}).get('id')), 202

    @app.post('/api/auth/signin')
    def signin():
        data = body()
        if data is None or not isinstance(data.get('email'), str) or not isinstance(data.get('password'), str):
            return jsonify(error='Email and password required'), 400
        result = supabase('POST', '/auth/v1/token?grant_type=password', json={
            'email': data['email'].strip(), 'password': data['password']})
        return jsonify(result)

    @app.post('/api/auth/refresh')
    def refresh():
        data = body()
        if data is None or not isinstance(data.get('refresh_token'), str) or not data['refresh_token']:
            return jsonify(error='refresh_token required'), 400
        return jsonify(supabase('POST', '/auth/v1/token?grant_type=refresh_token',
                                json={'refresh_token': data['refresh_token']}))

    @app.post('/api/auth/signout')
    @protected()
    def signout():
        supabase('POST', '/auth/v1/logout', g.token)
        return jsonify(message='Signed out. Discard stored tokens.')

    @app.get('/api/auth/me')
    @protected()
    def me():
        return jsonify(email=g.user['email'], **g.profile)

    @app.get('/api/admin/users')
    @protected('admin', 'super_admin')
    def users():
        try:
            offset = max(0, int(request.args.get('offset', 0)))
        except ValueError:
            return jsonify(error='offset must be an integer'), 400
        return jsonify(supabase('GET', '/rest/v1/profiles', g.token,
                               params={'select': 'id,full_name,role,created_at',
                                       'order': 'created_at.asc,id.asc', 'limit': 100, 'offset': offset}))

    @app.patch('/api/admin/users/<uuid:user_id>/role')
    @protected('super_admin')
    def change_role(user_id):
        data = body()
        if data is None or data.get('role') not in ('patient', 'doctor', 'admin', 'super_admin'):
            return jsonify(error='Valid role required'), 400
        supabase('POST', '/rest/v1/rpc/set_user_role', g.token,
                 json={'target_id': str(user_id), 'new_role': data['role']})
        return jsonify(message='Role updated')

    return app


app = create_app()
