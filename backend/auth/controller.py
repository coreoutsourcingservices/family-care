from flask import g, jsonify
from common.http import body
from common.security import protected
from auth import model


def session_payload(result):
    """Expose the Supabase session consistently without minting a second JWT."""
    session = result.get('session') or result
    return {key: session.get(key) for key in (
        'access_token', 'refresh_token', 'token_type', 'expires_in', 'expires_at')}


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
    tokens = session_payload(result)
    user = result.get('user') or (result.get('session') or {}).get('user') or {}
    user_id = user.get('id') or result.get('id')
    if tokens['access_token']:
        return jsonify(message='Signup successful.', user_id=user_id, user=user,
                       requires_email_confirmation=False, **tokens), 201
    return jsonify(message='Signup submitted. Confirm your email, then sign in to receive tokens.',
                   user_id=user_id, requires_email_confirmation=True, **tokens), 202

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
    return jsonify({**result, **session_payload(result)})

def refresh():
    data = body()
    if data is None or not isinstance(data.get('refresh_token'), str) or not data['refresh_token']:
        return jsonify(error='refresh_token required'), 400
    result = model.call('POST', '/auth/v1/token?grant_type=refresh_token',
                        json={'refresh_token': data['refresh_token']})
    return jsonify({**result, **session_payload(result)})

@protected()
def signout():
    model.call('POST', '/auth/v1/logout', g.token)
    return jsonify(message='Signed out. Discard stored tokens.')

@protected()
def me():
    return jsonify(email=g.user['email'], **g.profile)

