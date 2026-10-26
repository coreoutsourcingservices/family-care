from functools import wraps
from flask import g, jsonify, request
from common.supabase import supabase

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

