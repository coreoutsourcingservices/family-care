import re
from copy import deepcopy
from flask import jsonify, request
from core import schemas, care_schemas

EXAMPLES = {
    'Registration': {'full_name': 'Example User', 'email': 'user@example.com', 'mobile_number': '+919876543210',
                     'password': 'Choose-Your-Password8!', 'confirm_password': 'Choose-Your-Password8!'},
    'Login': {'email': 'user@example.com', 'password': 'Choose-Your-Password8!'},
    'SuperLogin': {'email': 'superadmin@example.com', 'password': 'Choose-Your-Password8!'},
    'VerifyOTP': {'challenge_token': '<challenge_token>', 'otp': '123456'},
    'Challenge': {'challenge_token': '<challenge_token>'},
    'ForgotPassword': {'email': 'user@example.com'},
    'Rejection': {'reason': 'Registration details require correction'},
    'RefreshRequest': {'refresh_token': '<refresh_token>'},
    'ChangePassword': {'current_password': 'Old-Password8!', 'new_password': 'New-Password8!', 'confirm_password': 'New-Password8!'},
}
EXAMPLES['CareProfileCreate'] = {'profile_type':'member','module':'child','full_name':'Aarav Kumar','date_of_birth':'2018-05-14','guardian_contact':'+919876543210','emergency_contacts':[],'referral_id':'rahulkumarD000001'}
EXAMPLES['CareProfileReferral'] = {'referral_id':'rahulkumarD000001'}
EXAMPLES['PatientRegistration'] = dict(EXAMPLES['Registration'], referral_id='rahulkumarD000001')
EXAMPLES['ConnectDoctor'] = {'referral_id': 'rahulkumarD000001'}
EXAMPLES['DoctorRegistration'] = dict(EXAMPLES['Registration'])
EXAMPLES['DoctorProfileSetup'] = dict(setup_token='<limited-purpose setup_token>', qualification='MBBS',
    medical_registration_number='EXAMPLE-12345', registering_council='Example Medical Council',
    specialization='General Medicine', address='Example Street, Delhi 110001',
    clinic_address='Example Clinic, Delhi 110001', years_of_experience=5)
EXAMPLES['ResetPassword'] = dict(EXAMPLES['VerifyOTP'], new_password='New-Password8!', confirm_password='New-Password8!')
EXAMPLES['InitialPassword'] = dict(EXAMPLES['ChangePassword'], challenge_token='<challenge_token>')
EXAMPLES['Resubmission'] = dict(EXAMPLES['Login'], qualification='MBBS', medical_registration_number='EXAMPLE-12345', registering_council='Example Medical Council')

SESSION = {'access_token': '<signed JWT>', 'refresh_token': '<opaque refresh token>', 'expires_in': 900,
           'token_type': 'Bearer', 'user': {'id': '<UUID>', 'public_id': 'C000001', 'role': 'PATIENT'}}
CHALLENGE = {'challenge_token': '<limited-purpose JWT>', 'expires_in': 300, 'resend_after': 60, 'email_status': 'queued'}


def success_examples(path, method='GET'):
    session = deepcopy(SESSION)
    namespace = path.split('/')[3] if len(path.split('/')) > 3 else ''
    roles = {'admin':('ADMIN','A000001'), 'superadmin':('SUPERADMIN','superadmin'), 'doctors':('DOCTOR','D000001'), 'patients':('PATIENT','C000001')}
    if namespace in roles:
        session['user'].update(role=roles[namespace][0], public_id=roles[namespace][1], full_name='Example User', email='user@example.com', phone_number='+919876543210', email_verified=True, approval_status='APPROVED', account_status='ACTIVE', must_change_password=False)
        if namespace == 'doctors':
            session['user']['referral_id'] = 'rahulkumarD000001'
        if namespace == 'patients':
            session['user']['referred_doctor'] = None
    if '/profiles' in path or '/care-profiles' in path:
        profile = {'id':'<profile UUID>','profile_type':'member','module':'child','full_name':'Aarav Kumar','date_of_birth':'2018-05-14','parent_profile_id':'<parent profile UUID>','doctor':None}
        report = {'id':'<report UUID>','profile_id':'<profile UUID>','name':'blood-test.pdf','storage_provider':'cloudinary','url':'<short-lived signed Cloudinary URL>','public_id':'familycare/C000001/profiles/<profile UUID>/child/reports/<report UUID>_blood-test.pdf','folder':'familycare/C000001/profiles/<profile UUID>/child/reports','resource_type':'raw','delivery_type':'authenticated','url_expires_in':300}
        if path.endswith('/reports'):
            return {201:{'report':report}} if method=='POST' else {200:{'items':[report],'total':1,'page':1,'per_page':25}}
        if path.endswith('/download'):
            return {200:{'report':report}}
        if path.endswith(('/profiles','/care-profiles')):
            return {201:{'profile':profile}} if method=='POST' else {200:{'items':[profile],'total':1,'page':1,'per_page':25}}
        return {200:{'profile':profile}}
    referral = {'referral_id': 'rahulkumarD000001', 'public_id': 'D000001', 'full_name': 'Dr Rahul Kumar',
                'email': 'rahul@example.com', 'mobile_number': '+919876543211',
                'account_status': 'ACTIVE', 'approval_status': 'APPROVED'}
    if path.endswith(('/doctors/referral', '/patients/doctor', '/patients/connect-doctor')):
        return {200: {'doctor': referral}}
    if path.endswith('/request-email-verification'):
        return {202: dict(CHALLENGE, email_status='sent')}
    if path.endswith('/health'):
        return {200: {'status': 'ok', 'service': 'familycare-backend', 'auth': 'flask-jwt'}}
    if path.endswith('/health/ready'):
        return {200: {'status': 'ready', 'database': 'postgresql'}}
    if path.endswith('/register'):
        return {202: dict(CHALLENGE, public_id=None, user_id=None, email_status='sent',
                          approval_status='PENDING_EMAIL_VERIFICATION',
                          message='OTP sent to your email. Verify OTP to complete registration.')}
    if path.endswith('/check') and '/admin/doctors/' in path:
        return {200: {'doctor_status': 'pending', 'cached': False,
                      'verification_check': {'checked_at': '<UTC timestamp>', 'requires_admin_review': True,
                                             'auto_approved': False, 'registration': {'status': 'manual_review'},
                                             'address': {'status': 'manual_review'},
                                             'clinic_postal': {'status': 'manual_review'},
                                             'clinic': {'status': 'manual_review'}}}}
    if path.endswith('/verify-email'):
        if '/doctors/' in path:
            return {202: {'requires_profile_setup': True, 'setup_token': '<limited-purpose setup_token>',
                          'user': {'approval_status': 'PROFILE_REQUIRED'}, 'doctor': {}}}
        return {200: session} if '/patients/' in path else {202: {'message': 'Email verified. Waiting for approval.',
                        'user': {'approval_status': 'PENDING_APPROVAL'}}}
    if path.endswith('/login'):
        if '/doctors/' in path:
            return {200: session, 202: {'requires_profile_setup': True, 'setup_token': '<limited-purpose setup_token>',
                                      'user': {'approval_status': 'PROFILE_REQUIRED'}}}
        if '/superadmin/' in path:
            return {200: session, 202: {'requires_password_change': True, 'challenge_token': '<challenge JWT>', 'expires_in': 600}}
        return {200: session}
    if path.endswith('/setup-profile'):
        return {202: {'message': 'Your profile is under review.', 'user': {'approval_status': 'PENDING_APPROVAL'}}}
    if path.endswith('/verify-login-otp'):
        return {410: {'error': {'code': 'login_otp_disabled', 'message': 'Sign in with email and password; login OTP is no longer required'}}}
    if path.endswith(('/initial-password', '/refresh')):
        return {200: session}
    if path.endswith('/resend-otp'):
        return {200: dict(CHALLENGE, email_status='sent')}
    if path.endswith('/forgot-password'):
        return {202: dict(CHALLENGE, message='If an eligible account exists, reset instructions are queued.')}
    messages = {'/api/v1/auth/logout':'Logged out', '/api/v1/auth/logout-all':'All sessions revoked', '/api/v1/auth/reset-password':'Password reset. Sign in again.', '/api/v1/auth/change-password':'Password changed. All sessions revoked; sign in again.'}
    if path in messages:
        return {200: {'message': messages[path]}}
    if path.endswith('/me'):
        return {200: {'user': session['user']}}
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
                                       for code, value in success_examples(path, method).items()}}
            for code, label in ((400, 'Invalid challenge/OTP/state'), (401, 'Invalid credentials/token/session'),
                                (403, 'Role, approval, status, transport or CSRF denied'), (404, 'Not found'),
                                (409, 'Duplicate data or invalid approval state'), (422, 'Validation failed'),
                                (429, 'Rate limit or OTP cooldown'), (413, 'Report exceeds size limit'), (415, 'Multipart upload required'), (502, 'Cloudinary upload failed'), (503, 'Database or Cloudinary unavailable/not configured')):
                operation['responses'][str(code)] = {'description': label, 'content': {'application/json': {
                    'example': {'error': {'code': 'error_code', 'message': label}}}}}
            for name in rule.arguments:
                operation['parameters'].append({'name': name, 'in': 'path', 'required': True, 'schema': {'type': 'string'},
                                               'description': 'UUID or public ID' if name == 'user_id' else 'Resource UUID'})
            if method == 'GET' and any(path.endswith(s) for s in ('-requests', '/admins', '/doctors', '/patients', '/audit-logs', '/profiles', '/care-profiles', '/reports')):
                operation['parameters'] += [dict(name='page', **{'in': 'query'}, schema={'type': 'integer', 'minimum': 1, 'default': 1}),
                                           dict(name='per_page', **{'in': 'query'}, schema={'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 25})]
            if method == 'GET' and path.endswith(('/profiles', '/care-profiles')):
                operation['parameters'].append({'name':'module','in':'query','schema':{'type':'string','enum':['child','adult','women']}})
            provided = meta.get('schema')
            name = provided.__name__ if isinstance(provided,type) else provided
            if name == 'ReportUpload':
                operation['requestBody'] = {'required': True, 'content': {'multipart/form-data': {'schema': {'type':'object','required':['file'],'properties':{'file':{'type':'string','format':'binary','description':'PDF/JPEG/PNG/WebP; max 10 MB'}}}}}}
            elif name:
                if name == 'RefreshRequest':
                    components[name] = {'type': 'object', 'additionalProperties': False, 'required': ['refresh_token'],
                                        'properties': {'refresh_token': {'type': 'string', 'maxLength': 512}}}
                else:
                    model = provided if isinstance(provided,type) else (getattr(schemas,name,None) or getattr(care_schemas,name))
                    definition = model.model_json_schema(ref_template='#/components/schemas/{model}')
                    components.update(definition.pop('$defs', {}))
                    components[name] = definition
                operation['requestBody'] = {'required': name != 'RefreshRequest', 'content': {'application/json': {
                    'schema': {'$ref': '#/components/schemas/'+name}, 'example': EXAMPLES.get(name,{})}}}
            if meta.get('roles'):
                operation['security'] = [{'bearerAuth': []}, {'cookieAuth': []}]
            operation['parameters'] += [{'name': 'X-Auth-Transport', 'in': 'header', 'schema': {'type': 'string', 'enum': ['bearer', 'cookie'], 'default': 'bearer'}},
                                       {'name': 'X-FamilyCare-Portal', 'in': 'header', 'schema': {'type': 'string', 'enum': ['patient','doctor']}, 'description': 'Public cookie clients select their independent patient or doctor session; omit for bearer clients and admin proxy.'},
                                       {'name': 'X-Requested-With', 'in': 'header', 'schema': {'type': 'string'}, 'description': 'FamilyCare; required for cookie POST/DELETE'},
                                       {'name': 'X-CSRF-Token', 'in': 'header', 'schema': {'type': 'string'}, 'description': 'Required on authenticated cookie mutations and refresh'}]
            paths.setdefault(path, {})[method.lower()] = operation
    from core.api_contracts import enrich
    enrich(paths,components)
    from core.family_contracts import enrich as family_contracts
    family_contracts(paths)
    from core.growth_nutrition_contracts import enrich as growth_contracts
    growth_contracts(paths)
    return {'openapi': '3.1.0', 'info': {'title': 'Family Care Backend API', 'version': '1.0.0',
                'description': 'Flask backend APIs. Next.js admin/superadmin app runs on port 3005. Cookie sessions omit tokens from JSON.'},
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
