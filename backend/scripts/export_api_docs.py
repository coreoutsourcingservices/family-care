"""Generate the API contract, Markdown reference and Postman collection from registered routes."""
import json
from pathlib import Path
from app import create_app
from core.openapi import specification, EXAMPLES


def main():
    app = create_app()
    spec = specification(app)
    root = Path(__file__).resolve().parents[1] / 'docs'
    root.mkdir(exist_ok=True)
    (root / 'openapi.json').write_text(json.dumps(spec, indent=2), encoding='utf-8')
    lines = ['# Family Care API reference', '', 'Base URL: `http://127.0.0.1:5001` (local only).', '',
             'API only: no website, dashboard UI or mobile UI is included.', '',
             'OpenAPI: `GET /api/openapi.json`. JSON API index: `GET /api/docs`.', '',
             'All JSON requests use `Content-Type: application/json`.',
             'Mobile/CLI: `Authorization: Bearer <access_token>` for protected endpoints.',
             'Browser: `X-Auth-Transport: cookie`, credentials enabled, `X-Requested-With: FamilyCare` on mutations;',
             'also send the returned `csrf_token` as `X-CSRF-Token` on authenticated mutations and refresh.',
             'Cookie sessions return no access/refresh tokens in JSON. Refresh rotates the CSRF token too.', '',
             'Passwords: 8–128 characters; `confirm_password` must match. Roles/public IDs/status are server owned.',
             'All dates are stored as UTC. Public IDs or UUIDs may be used for `{user_id}`.',
             'List routes support `page=1&per_page=25` (maximum 100); user lists accept `status` approval filter.', '',
             'Signup sends email OTP synchronously and stores temporary details in a TTL cache, not PostgreSQL.',
             'No user/profile/OTP/audit/outbox rows are inserted until signup OTP verification succeeds.',
             'Register returns null public_id/user_id; IDs are assigned only after verification.',
             'SMTP acceptance returns email_status sent; delivery failure returns 503 email_delivery_failed.',
             'Patient verification issues a JWT session; admin/doctor verification queues approval.',
             'Admin and patient login: password → OTP → session. Doctor login: password → session after approval.',
             'Superadmin first login: password → initial-password challenge → password rotation → session.', '',
             'OTP: 6 digits, 5 minutes, 60-second resend cooldown, 5 attempts, one-time use.',
             'After a consumed/exhausted signup challenge, restart with `/auth/request-email-verification`.',
             'Forgot password is generic for unknown accounts. Registration conflicts can reveal existing accounts.',
             'Signup mail is sent directly; sent means SMTP accepted it, not a guarantee of inbox placement.',
             'Login/reset/approval mail still uses the outbox and requires the separate SMTP worker.', '',
             'Access JWT default: 15 minutes. Refresh session: 7 days with rotation and replay revocation.',
             'Logout, suspension and password change revoke sessions; reactivation does not restore old sessions.',
             'On concurrent refresh, only one succeeds; reuse revokes that session. Clients must serialize refresh.', '',
             '## All API URLs', '', '| Method | Local URL | Access |', '|---|---|---|']
    collection = {'info': {'name': 'Family Care API v1', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
                  'variable': [{'key': 'base_url', 'value': 'http://127.0.0.1:5001'}, {'key': 'access_token', 'value': ''},
                               {'key': 'user_id', 'value': ''}, {'key': 'session_id', 'value': ''}], 'item': []}
    for path, methods in spec['paths'].items():
        for method, operation in methods.items():
            lines.append(f'| {method.upper()} | `http://127.0.0.1:5001{path}` | {operation["description"]} |')
    for path, methods in spec['paths'].items():
        for method, operation in methods.items():
            lines += ['', f'## {method.upper()} {path}', '', operation['description'], '']
            body = operation.get('requestBody', {}).get('content', {}).get('application/json', {})
            example = body.get('example')
            if example:
                schema_name = body['schema']['$ref'].rsplit('/', 1)[-1]
                schema = spec['components']['schemas'][schema_name]
                lines += ['Request fields:', '', '| Field | Required | Validation |', '|---|---|---|']
                for field, definition in schema.get('properties', {}).items():
                    checks = {k: v for k,v in definition.items() if k not in ('title',)}
                    lines.append(f'| `{field}` | {"yes" if field in schema.get("required",[]) else "no"} | `{json.dumps(checks)}` |')
                lines += ['', 'Request JSON:', '', '```json', json.dumps(example, indent=2), '```']
            else:
                lines += ['No JSON body required.']
            for status, response in operation['responses'].items():
                lines += ['', f'HTTP {status}: {response["description"]}', '', '```json',
                          json.dumps(response['content']['application/json']['example'], indent=2), '```']
            headers = [{'key': 'Content-Type', 'value': 'application/json'}]
            if operation.get('security'):
                headers.append({'key': 'Authorization', 'value': 'Bearer {{access_token}}'})
            request = {'method': method.upper(), 'header': headers,
                       'url': '{{base_url}}'+path.replace('{user_id}', '{{user_id}}').replace('{session_id}', '{{session_id}}')}
            if example:
                request['body'] = {'mode': 'raw', 'raw': json.dumps(example, indent=2), 'options': {'raw': {'language': 'json'}}}
            collection['item'].append({'name': operation['summary'], 'request': request})
            flutter_data = json.dumps(example) if example else '{}'
            lines += ['', 'Flutter (Dio; use the refresh-aware client in `examples/flutter_api.dart`):', '', '```dart',
                      f"await dio.request('{path}', data: {flutter_data}, options: Options(method: '{method.upper()}'));", '```',
                      '', 'Web (use the cookie/CSRF client in `examples/web_api.js`):', '', '```javascript',
                      f"await api('{path}', '{method.upper()}', {json.dumps(example) if example else 'undefined'});", '```']
    (root / 'API_DOCUMENTATION.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (root / 'postman_collection.json').write_text(json.dumps(collection, indent=2), encoding='utf-8')
    print('Exported API Markdown, OpenAPI and Postman collection.')


if __name__ == '__main__':
    main()
