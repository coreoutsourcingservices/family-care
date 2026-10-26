import re
from flask import jsonify, request
from core import schemas

EXAMPLES = {
    'Registration': {'full_name': 'Example User', 'email': 'user@example.com', 'mobile_number': '+919876543210',
                     'password': 'Choose-Your-Password8!', 'confirm_password': 'Choose-Your-Password8!'},
    'Login': {'email': 'user@example.com', 'password': 'Choose-Your-Password8!'},
    'SuperLogin': {'username': 'superadmin', 'password': 'superadmin@2026'},
    'VerifyOTP': {'challenge_token': '<challenge_token>', 'otp': '123456'},
    'Challenge': {'challenge_token': '<challenge_token>'},
    'ForgotPassword': {'email': 'user@example.com'},
    'Rejection': {'reason': 'Registration details require correction'},
    'RefreshRequest': {'refresh_token': '<refresh_token>'},
    'ChangePassword': {'current_password': 'Old-Password8!', 'new_password': 'New-Password8!', 'confirm_password': 'New-Password8!'},
}
EXAMPLES['DoctorRegistration'] = dict(EXAMPLES['Registration'], qualification='MBBS',
    medical_registration_number='EXAMPLE-12345', registering_council='Example Medical Council', specialization='General Medicine')
EXAMPLES['ResetPassword'] = dict(EXAMPLES['VerifyOTP'], new_password='New-Password8!', confirm_password='New-Password8!')
EXAMPLES['InitialPassword'] = dict(EXAMPLES['ChangePassword'], challenge_token='<challenge_token>')
EXAMPLES['Resubmission'] = dict(EXAMPLES['Login'], qualification='MBBS', medical_registration_number='EXAMPLE-12345', registering_council='Example Medical Council')

SESSION = {'access_token': '<signed JWT>', 'refresh_token': '<opaque refresh token>', 'expires_in': 900,
           'token_type': 'Bearer', 'user': {'id': '<UUID>', 'public_id': 'C000001', 'role': 'PATIENT'}}
CHALLENGE = {'challenge_token': '<limited-purpose JWT>', 'expires_in': 300, 'resend_after': 60, 'email_status': 'queued'}


def success_examples(path):
    if path.endswith('/request-email-verification'):
        return {202: CHALLENGE}
    if path.endswith('/health'):
        return {200: {'status': 'ok', 'service': 'familycare-backend', 'auth': 'flask-jwt'}}
    if path.endswith('/health/ready'):
        return {200: {'status': 'ready', 'database': 'postgresql'}}
    if path.endswith('/register'):
        return {202: dict(CHALLENGE, public_id='D000001' if '/doctors/' in path else 'A000001' if '/admin/' in path else 'C000001',
                          user_id='<UUID>', approval_status='PENDING_EMAIL_VERIFICATION')}
    if path.endswith('/verify-email'):
        return {200: SESSION} if '/patients/' in path else {202: {'message': 'Email verified. Waiting for approval.',
                        'user': {'approval_status': 'PENDING_APPROVAL'}}}
    if path.endswith('/login'):
        if '/superadmin/' in path:
            return {200: SESSION, 202: {'requires_password_change': True, 'challenge_token': '<challenge JWT>', 'expires_in': 600}}
        return {200: SESSION} if '/doctors/' in path else {202: dict(CHALLENGE, requires_otp=True)}
    if path.endswith(('/verify-login-otp', '/initial-password', '/refresh')):
        return {200: SESSION}
    if path.endswith('/resend-otp'):
        return {200: CHALLENGE}
    if path.endswith('/forgot-password'):
        return {202: dict(CHALLENGE, message='If an eligible account exists, reset instructions are queued.')}
    if path.endswith('/me'):
        return {200: {'user': SESSION['user']}}
    if path.endswith('/approval-status'):
        return {200: {'public_id': 'D000001', 'email_verified': True, 'approval_status': 'PENDING_APPROVAL',
                       'account_status': 'ACTIVE', 'rejection_reason': None}}
    if path.endswith('/resubmit'):
        return {202: {'message': 'Resubmitted for review', 'user': {'approval_status': 'PENDING_APPROVAL'}}}
    if path.endswith(('/approve', '/reject')):
        return {200: {'user': {'approval_status': 'APPROVED' if path.endswith('/approve') else 'REJECTED'}, 'email_status': 'queued'}}
    if path.endswith(('/suspend', '/reactivate')):
        return {200: {'user': {'account_status': 'SUSPENDED' if path.endswith('/suspend') else 'ACTIVE'}}}
    if path.endswith('/dashboard'):
        return {200: {'counts': [{'role': 'ADMIN', 'approval_status': 'PENDING_APPROVAL', 'count': 1}]}}
    if path.endswith(('/admins', '/doctors', '/patients', '-requests', '/audit-logs', '/sessions')):
        return {200: {'items': [], 'total': 0}}
    return {200: {'message': 'Operation completed'}}


def specification(app):
    components = {}
    paths = {}
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/api/v1'):
            continue
        meta = getattr(app.view_functions[rule.endpoint], 'api_meta', {})
        path = re.sub(r'<(?:\w+:)?(\w+)>', r'{\1}', rule.rule)
        for method in sorted(rule.methods - {'HEAD', 'OPTIONS'}):
            operation = {'operationId': rule.endpoint.replace('.', '_'), 'tags': [path.split('/')[3]],
                         'summary': rule.endpoint.replace('.', ' ').replace('_', ' '), 'parameters': [],
                         'description': 'Required roles: '+(', '.join(meta.get('roles') or []) or 'public / limited challenge'),
                         'responses': {str(code): {'description': 'Success', 'content': {'application/json': {'example': value}}}
                                       for code, value in success_examples(path).items()}}
            for code, label in ((400, 'Invalid challenge/OTP/state'), (401, 'Invalid credentials/token/session'),
                                (403, 'Role, approval, status, transport or CSRF denied'), (404, 'Not found'),
                                (409, 'Duplicate data or invalid approval state'), (422, 'Validation failed'),
                                (429, 'Rate limit or OTP cooldown'), (503, 'Database unavailable/not configured')):
                operation['responses'][str(code)] = {'description': label, 'content': {'application/json': {
                    'example': {'error': {'code': 'error_code', 'message': label}}}}}
            for name in rule.arguments:
                operation['parameters'].append({'name': name, 'in': 'path', 'required': True, 'schema': {'type': 'string'},
                                               'description': 'UUID or public ID' if name == 'user_id' else 'Session UUID'})
            if method == 'GET' and any(path.endswith(s) for s in ('-requests', '/admins', '/doctors', '/patients', '/audit-logs')):
                operation['parameters'] += [dict(name='page', **{'in': 'query'}, schema={'type': 'integer', 'minimum': 1, 'default': 1}),
                                           dict(name='per_page', **{'in': 'query'}, schema={'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 25})]
            name = meta.get('schema')
            if name:
                if name == 'RefreshRequest':
                    components[name] = {'type': 'object', 'additionalProperties': False, 'required': ['refresh_token'],
                                        'properties': {'refresh_token': {'type': 'string', 'maxLength': 512}}}
                else:
                    components[name] = getattr(schemas, name).model_json_schema()
                operation['requestBody'] = {'required': name != 'RefreshRequest', 'content': {'application/json': {
                    'schema': {'$ref': '#/components/schemas/'+name}, 'example': EXAMPLES[name]}}}
            if meta.get('roles'):
                operation['security'] = [{'bearerAuth': []}, {'cookieAuth': []}]
            operation['parameters'] += [{'name': 'X-Auth-Transport', 'in': 'header', 'schema': {'type': 'string', 'enum': ['bearer', 'cookie'], 'default': 'bearer'}},
                                       {'name': 'X-Requested-With', 'in': 'header', 'schema': {'type': 'string'}, 'description': 'FamilyCare; required for cookie POST/DELETE'},
                                       {'name': 'X-CSRF-Token', 'in': 'header', 'schema': {'type': 'string'}, 'description': 'Required on authenticated cookie mutations and refresh'}]
            paths.setdefault(path, {})[method.lower()] = operation
    return {'openapi': '3.1.0', 'info': {'title': 'Family Care Backend API', 'version': '1.0.0',
                'description': 'API only. Flask owns authentication. No frontend UI. Cookie sessions omit tokens from JSON.'},
            'servers': [{'url': 'http://127.0.0.1:5001', 'description': 'Local development'}], 'paths': paths,
            'components': {'schemas': components, 'securitySchemes': {
                'bearerAuth': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'},
                'cookieAuth': {'type': 'apiKey', 'in': 'cookie', 'name': 'fc_access'}}}}


def install_docs(app):
    @app.get('/api/openapi.json')
    def openapi():
        return jsonify(specification(app))

    @app.get('/api/docs')
    def docs():
        return jsonify(title='Family Care API documentation (API only)', openapi='/api/openapi.json',
                       endpoints=[{'method': m.upper(), 'url': path, 'roles': item.get('description')}
                                  for path, methods in specification(app)['paths'].items() for m, item in methods.items()])
