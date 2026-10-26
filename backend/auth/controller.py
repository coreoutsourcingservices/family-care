from flask import g, jsonify
from common.http import body
from common.security import protected
from auth import model

def signup(role_override=None):
    data = body()
    if data is None:
        return jsonify(error='JSON object required'), 400
    email, password = data.get('email'), data.get('password')
    name, role = data.get('full_name'), role_override or data.get('role', 'patient')
    if role_override and data.get('role', role_override) != role_override:
        return jsonify(error='Role does not match signup endpoint'), 400
    if role not in ('patient', 'doctor'):
        return jsonify(error='Public signup allows patient or doctor only'), 400
    if (not isinstance(email, str) or '@' not in email or len(email) > 254
            or not isinstance(password, str) or not 12 <= len(password) <= 128
            or not isinstance(name, str) or not 1 <= len(name.strip()) <= 120):
        return jsonify(error='Valid email, full_name and password (12–128 characters) required'), 400
    result = model.call('POST', '/auth/v1/signup', json={
        'email': email.strip(), 'password': password,
        'data': {'full_name': name.strip(), 'role': role}})
    return jsonify(message='Signup submitted. Check your email to confirm your account.',
                   user_id=result.get('id') or result.get('user', {}).get('id')), 202

def signin(expected_role=None):
    data = body()
    if data is None or not isinstance(data.get('email'), str) or not isinstance(data.get('password'), str):
        return jsonify(error='Email and password required'), 400
    result = model.call('POST', '/auth/v1/token?grant_type=password', json={
        'email': data['email'].strip(), 'password': data['password']})
    if expected_role:
        profile = model.profile(result['user']['id'], result['access_token'])
        if not profile or profile['role'] != expected_role:
            return jsonify(error='Account role does not match this signin endpoint'), 403
    return jsonify(result)

def refresh():
    data = body()
    if data is None or not isinstance(data.get('refresh_token'), str) or not data['refresh_token']:
        return jsonify(error='refresh_token required'), 400
    return jsonify(model.call('POST', '/auth/v1/token?grant_type=refresh_token',
                            json={'refresh_token': data['refresh_token']}))

@protected()
def signout():
    model.call('POST', '/auth/v1/logout', g.token)
    return jsonify(message='Signed out. Discard stored tokens.')

@protected()
def me():
    return jsonify(email=g.user['email'], **g.profile)

