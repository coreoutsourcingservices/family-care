"""Export every registered API method without overwriting existing documentation."""
import sys,json,re
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from core.openapi import specification

def main():
    app=create_app();spec=specification(app)
    root=Path(__file__).resolve().parents[2]/'api-reference';root.mkdir(exist_ok=True)
    (root/'openapi.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# FamilyCare: all API methods','',
      'Base URL: `http://127.0.0.1:5001`. All registered GET/POST/PUT/PATCH/DELETE methods are listed below. Examples use synthetic values, not patient data. Replace UUIDs, tokens and example fields. JSON Schema contains validation constraints; a sample is not a clinical recommendation.','',
      '## Login and portal integration','',
      '| UI | URL | Backend login |','| --- | --- | --- |',
      '| Public frontend | http://127.0.0.1:5173 | Links to customer/doctor flows |',
      '| Customer frontend | http://127.0.0.1:5174/customer/login | POST /api/v1/patients/login |',
      '| Doctor frontend | http://127.0.0.1:5175/doctor/login | POST /api/v1/doctors/login |',
      '| Admin | http://127.0.0.1:3005 | POST /api/v1/admin/login |',
      '| Superadmin | http://127.0.0.1:3005/superadmin | POST /api/v1/superadmin/login |','',
      'Web uses role-scoped HttpOnly cookie sessions. Send `X-Auth-Transport: cookie`, `X-Requested-With: FamilyCare`, credentials include and `X-CSRF-Token` for authenticated mutations. App clients use `X-Auth-Transport: bearer` and `Authorization: Bearer <access_token>`. Never mix transports. JSON requests use Content-Type application/json; file uploads use multipart/form-data without manually setting its boundary.','',
      'Doctor login can return 202 for profile setup/review instead of a clinical access session. Follow `requires_profile_setup`, `setup_token` and approval status. Setup tokens authorize setup only. Notification tokens authorize the doctor notification inbox only. Standard access tokens authorize role-protected clinical/profile APIs.','',
      '## UI coverage and method availability','',
      '- Doctor Settings: authenticated profile-photo upload/replace/remove; header and connected-family cards use the saved photo. Setup additionally supports private degree documents. Signed image URLs last five minutes; refresh the owning profile endpoint to renew them.',
      '- Admin and superadmin: Doctors list links to `/doctors/{public_id}` within the portal. Full profile and paginated connected-family metadata load from separate API endpoints. Approval/suspension remains a deliberate role-bound action.',
      '- Customer child diary: list/create/edit/delete for vaccination history, medical history, growth, nutrition, consultations, care notes and consultation requests. Single-record GETs support deep-link clients.',
      '- Customer adult diary: list/create, single-record GET, PATCH update and DELETE. Existing POST update/delete aliases remain compatible. PATCH currently expects the complete editable record body.',
      '- Connected doctor removal uses DELETE on the selected profile and immediately revokes that doctor\'s access to that profile.',
      '- Child/adult Settings: edit profile name/contact via PUT /patients/profiles/{profile_id}; DOB, ownership, profile type and medical approval identity are not writable through this endpoint.',
      '- Vaccine catalog/schedules use drafts, independent medical review and administrator publication. Clinical history and published versions do not get arbitrary account-wide delete methods.',
      '- Methods absent from the matrix are not implemented. A list-only or approval resource does not gain POST/DELETE just because another resource supports CRUD. Women profiles use shared profile/report/referral APIs; there is no invented women diary endpoint.',
      '- Customer and approved doctor portals connect to /ws/notifications using a short-lived POST /notifications/socket-ticket ticket in the first auth frame. REST polling resynchronizes the inbox. Closed-app mobile push requires a separate device-push service.','',
      '## Reading this single-file reference','',
      'Generated on '+datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')+'. This file includes every versioned REST operation, request examples, response examples, validation schemas, upload limits and realtime integration. Examples are synthetic contracts, not captured production responses. An endpoint appearing here does not mean its external SMTP, storage or OCR provider has been tested live. Path placeholders must be replaced with accessible resource IDs. Response examples show representative shapes; optional values depend on the record and account state.','',
      'For cookie authentication, public portals also send `X-FamilyCare-Portal: patient` or `doctor` on every request, including login and refresh. This keeps the two sessions independent. Bearer clients omit this header.','',
      '## Upload sizes and file response data','',
      '| Data | Limit / format |','| --- | --- |',
      '| Ordinary request body | 16,384 bytes (16 KiB), unless the upload route overrides it |',
      '| Patient profile health report | 10 MiB (10,485,760 bytes); PDF, JPEG, PNG or WebP; multipart field `file` |',
      '| Doctor setup / profile image | 5 MiB (5,242,880 bytes); JPEG, PNG or WebP; multipart field `file` |',
      '| Report upload request overhead | Up to 65,536 extra bytes beyond the report limit for multipart framing |',
      '| Image upload request overhead | Up to 65,536 extra bytes beyond the image limit for multipart framing |','',
      'Upload JSON responses return metadata and, when configured, a temporary signed URL; they do not embed the original file bytes or base64. Download endpoints can return binary content: check the response Content-Type and Content-Disposition rather than parsing every response as JSON. Signed URLs expire; request fresh metadata to renew access. See each upload operation for its additional form fields and authentication. MB labels in the UI use the binary limits above.','',
      '## Implemented workflows','',
      '- Patient: register -> signup email OTP -> verify -> login -> create self/member profile -> use child/adult records, reports, referral and notifications.',
      '- Doctor: register -> signup OTP -> setup profile/images -> admin review -> approved clinical login -> connected profiles, records, vaccination review and notifications.',
      '- Admin/superadmin: login -> review accounts -> manage vaccine catalogue, schedule drafts, independent medical review, publication and visibility.',
      '- Every child can read active UIP/IAP plans without a doctor referral. Dates derive from that child\'s DOB. Unpublished entries remain Doctor Review; completion records and doctor applicability decisions remain child-specific. Switching children retains the selected page.',
      '- Reports: upload -> request extraction -> poll job -> optionally request translation with explicit consent -> review extracted values before importing a diary record. OCR and translation are separate operations.',
      '- Women profiles use the shared profile, referral and report APIs. Only the methods in the inventory are implemented.','',
      '## Every registered resource and verb','', '| Path | GET | POST | PUT | PATCH | DELETE |','| --- | --- | --- | --- | --- | --- |']
    collection={'info':{'name':'FamilyCare complete API','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},'variable':[{'key':'base_url','value':'http://127.0.0.1:5001'},{'key':'access_token','value':''},{'key':'notification_token','value':''}],'item':[]}
    for path,methods in sorted(spec['paths'].items()):lines.append('| `'+path+'` | '+' | '.join('Yes' if verb in methods else '—' for verb in ('get','post','put','patch','delete'))+' |')
    count=0
    for path,methods in sorted(spec['paths'].items()):
      for method,op in methods.items():
        count+=1
        lines+=['',f'## {method.upper()} {path}','',op['description'],'',f'URL: `http://127.0.0.1:5001{path}`','']
        params=op.get('parameters',[])
        if params:
          lines+=['| Parameter | Location | Required | Schema |','| --- | --- | --- | --- |']
          for p in params:lines.append(f"| `{p['name']}` | {p['in']} | {p.get('required',False)} | `{json.dumps(p.get('schema',{}))}` |")
        content=op.get('requestBody',{}).get('content',{})
        request={'method':method.upper(),'url':'{{base_url}}'+re.sub(r'{(\w+)}',r'{{\1}}',path),'header':[{'key':'X-Auth-Transport','value':'bearer'}]}
        if op.get('security'):request['header'].append({'key':'Authorization','value':'Bearer {{notification_token}}' if '/doctors/notifications' in path else 'Bearer {{access_token}}'})
        if 'multipart/form-data' in content:
          schema=content['multipart/form-data']['schema'];lines+=['','Request: **multipart/form-data**','', '```json',json.dumps(schema,indent=2),'```']
          lines+=['','Form data example (send the file as binary, not as JSON):','','```json',json.dumps({k:('<binary file: example.pdf or example.png>' if v.get('format')=='binary' else v.get('example',v.get('default','<'+k+'>'))) for k,v in schema.get('properties',{}).items()},indent=2),'```']
          request['body']={'mode':'formdata','formdata':[{'key':k,'type':'file' if v.get('format')=='binary' else 'text','value':''} for k,v in schema.get('properties',{}).items()]}
        elif 'application/json' in content:
          payload=content['application/json'];example=payload.get('example',{})
          lines+=['','Request: **application/json**','', '```json',json.dumps(example,indent=2,ensure_ascii=False),'```']
          ref=payload.get('schema',{}).get('$ref','').rsplit('/',1)[-1]
          if ref:lines+=['',f'Validation schema: `{ref}` (included in openapi.json).','', '```json',json.dumps(spec['components']['schemas'][ref],indent=2,ensure_ascii=False),'```']
          else:lines+=['','Validation schema:','','```json',json.dumps(payload.get('schema',{}),indent=2,ensure_ascii=False),'```']
          request['header'].append({'key':'Content-Type','value':'application/json'});request['body']={'mode':'raw','raw':json.dumps(example,indent=2),'options':{'raw':{'language':'json'}}}
        else:lines+=['Request body: none, or `{}` for a bodyless POST action.']
        for status,response in op['responses'].items():
          lines+=['',f"HTTP {status} — {response['description']}",'','```json',json.dumps(response.get('content',{}).get('application/json',{}).get('example',{}),indent=2,ensure_ascii=False),'```']
        lines+=['','Common failure responses: 400 invalid input/transport; 401 invalid session; 403 role/CSRF; 404 inaccessible or missing resource; 409 state conflict; 413 upload size; 422 validation; 429 throttled; 502/503 upstream/storage/database unavailable. Only failures applicable to this endpoint occur.','', '```json','{"error":{"code":"validation_error","message":"Invalid request fields","fields":[{"field":"title","type":"missing"}]}}','```']
        responses=[{'name':status+' example','originalRequest':request,'status':response['description'],'code':int(status),'header':[{'key':'Content-Type','value':'application/json'}],'body':json.dumps(response.get('content',{}).get('application/json',{}).get('example',{}),indent=2,ensure_ascii=False)} for status,response in op['responses'].items()]
        collection['item'].append({'name':method.upper()+' '+path,'request':request,'response':responses})
    for filename in ('CHILD_PLAN_ACTIVATION.md','PUBLIC_PORTAL_SESSIONS.md','REALTIME_NOTIFICATIONS.md','woman_adule_api.md'):
      source=root/filename
      if source.exists():
        lines+=['','## Integration notes: '+filename,'',re.sub(r'^(#+) ',r'##\1 ',source.read_text(encoding='utf-8'),flags=re.M)]
    lines+=['','## Complete validation schema appendix','','All referenced component schemas are included below so this Markdown file can be shared on its own. `$ref` values point to another named schema in this appendix.']
    for name,schema in sorted(spec['components']['schemas'].items()):
      lines+=['',f'### Schema: {name}','','```json',json.dumps(schema,indent=2,ensure_ascii=False),'```']
    lines+=['','## Operational endpoints outside the versioned REST inventory','','- `GET /health`: liveness; example `{"auth":"flask-jwt","service":"familycare-backend","status":"ok"}`.','- `GET /api/v1/health/ready`: database/schema readiness; documented in the inventory.','- `GET /api/docs`: JSON route inventory.','- `GET /api/openapi.json`: OpenAPI JSON contract.','- WebSocket `/ws/notifications`: see realtime integration above; not a REST method.','','## Files and regeneration','','- `ALL_APIS.md`: this complete single-file human-readable reference.','- `openapi.json`: machine-readable companion.','- `postman_collection.json`: importable request collection.','- Regenerate: from backend, `venv/Scripts/python.exe scripts/export_full_api.py`.','',f'Total registered API method operations: **{count}**.']
    (root/'ALL_APIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (root/'postman_collection.json').write_text(json.dumps(collection,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Exported {count} operations to {root}')

if __name__=='__main__':main()
