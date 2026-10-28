"""Synthetic doctor API documentation exporter. Isolated SQLite; no live writes/SMTP."""
import sys,json,time
from pathlib import Path
from datetime import timedelta
sys.path.insert(0,str(Path(__file__).resolve().parent))
from frontend_fixture import app
from core.database import db
from core.models import User,DoctorProfile,CareReport,OTPChallenge,now
from core.security import decode_token
from services.otp import otp_code
from patient.child_routes import today
from sqlalchemy import select
ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'backend/docs'
client=app.test_client();examples=[];password='SmokePassword8!'
with app.app_context():
    doctor=db().scalar(select(User).where(User.role=='DOCTOR'));doctor.full_name='Dr Example Kumar';doctor.public_id='D000001';doctor.approval_status='APPROVED'
    professional=db().get(DoctorProfile,doctor.id);professional.referral_id='examplekumarD000001';professional.verification_status='APPROVED'
    patient=db().scalar(select(User).where(User.role=='PATIENT'));patient.public_id='C000001';patient.full_name='Example Parent'
    doctor_id=doctor.id;patient_id=patient.id;referral=professional.referral_id;db().commit()
def auth(data):return {'Authorization':'Bearer '+data['access_token']}
def login(role='doctors'):
    response=client.post('/api/v1/'+role+'/login',json={'email':{'doctors':'doctor@example.com','patients':'patient@example.com','admin':'admin@example.com'}[role],'password':password if role=='doctors' else 'SmokePassword8!'})
    assert response.status_code==200,response.json
    return response.json
def call(name,method,path,body=None,session=None,role='DOCTOR',expected=200):
    response=client.open('/api/v1'+path,method=method,json=body,headers=auth(session) if session else {})
    assert response.status_code==expected,(name,response.status_code,response.json)
    examples.append(dict(name=name,method=method,url='http://127.0.0.1:5001/api/v1'+path,auth=role if session else 'PUBLIC',request_json=body,response_status=response.status_code,response_json=response.json))
    return response.json
def age_pending():
    for item in app.extensions['pending_signups'].items.values():item['sent_at']=time.time()-61
def code(token):
    with app.app_context():return otp_code(decode_token(token,'challenge')['cid'])
registration=dict(full_name='Dr New Example',email='new-doctor@example.com',mobile_number='+919876543219',password='ExamplePass8!',confirm_password='ExamplePass8!',qualification='MBBS',medical_registration_number='DEMO-12345',registering_council='Example Council',specialization='Pediatrics')
pending=call('Doctor registration','POST','/doctors/register',registration,expected=202)
age_pending();pending=call('Doctor resend email OTP','POST','/doctors/resend-otp',{'challenge_token':pending['challenge_token']})
age_pending();pending=call('Restart pending email verification','POST','/auth/request-email-verification',{'email':registration['email'],'password':registration['password']},expected=202)
verified=call('Verify doctor email','POST','/doctors/verify-email',{'challenge_token':pending['challenge_token'],'otp':code(pending['challenge_token'])},expected=202)
call('Doctor approval status','POST','/doctors/approval-status',{'email':registration['email'],'password':registration['password']})
with app.app_context():db().get(User,verified['user']['id']).approval_status='REJECTED';db().commit()
call('Resubmit rejected doctor application','POST','/doctors/resubmit',{'email':registration['email'],'password':registration['password'],'qualification':'MBBS','medical_registration_number':'DEMO-12345-CORRECTED','registering_council':'Example Council'},expected=202)
session=call('Doctor login - Bearer response','POST','/doctors/login',{'email':'doctor@example.com','password':password})
call('Doctor profile','GET','/doctors/me',session=session)
call('Own doctor referral ID','GET','/doctors/referral',session=session)
parent=login('patients')
new_parent=call('New patient signup with doctor referral','POST','/patients/register',{'full_name':'New Example Parent','email':'new-parent@example.com','mobile_number':'+919876543218','password':'ExampleParent8!','confirm_password':'ExampleParent8!','referral_id':referral},expected=202)
call('Verify referred patient signup','POST','/patients/verify-email',{'challenge_token':new_parent['challenge_token'],'otp':code(new_parent['challenge_token'])})
call('Connect parent account using referral','POST','/patients/connect-doctor',{'referral_id':referral},session=parent,role='PATIENT')
call('Parent connected doctor','GET','/patients/doctor',session=parent,role='PATIENT')
profile=call('Create child profile with referral','POST','/patients/profiles',{'profile_type':'member','module':'child','full_name':'Example Child','date_of_birth':'2020-03-01','guardian_contact':'+919876543210','emergency_contacts':[],'referral_id':referral},session=parent,role='PATIENT',expected=201)['profile'];profile_id=profile['id']
call('Connect existing family profile using referral','POST',f'/patients/profiles/{profile_id}/connect-doctor',{'referral_id':referral},session=parent,role='PATIENT')
call('Doctor connected patient accounts','GET','/doctors/patients?page=1&per_page=25',session=session)
call('Doctor connected child care profiles','GET','/doctors/care-profiles?module=child&page=1&per_page=25',session=session)
call('Doctor care profile detail','GET',f'/doctors/care-profiles/{profile_id}',session=session)
with app.app_context():
    app.config.update(CLOUDINARY_CLOUD_NAME='example-cloud',CLOUDINARY_API_KEY='example-key',CLOUDINARY_API_SECRET='example-secret')
    report=CareReport(profile_id=profile_id,name='Example report.pdf',content_type='application/pdf',storage_provider='cloudinary',cloudinary_public_id='synthetic/example.pdf',secure_url='https://res.cloudinary.com/example-cloud/raw/authenticated/synthetic/example.pdf',resource_type='raw',delivery_type='authenticated',file_format='pdf',size_bytes=1024)
    db().add(report);db().commit();report_id=report.id
call('Doctor reports list','GET',f'/doctors/care-profiles/{profile_id}/reports?page=1&per_page=25',session=session)
call('Doctor report download JSON','GET',f'/doctors/care-profiles/{profile_id}/reports/{report_id}/download',session=session)
call('Parent sends consultation request','POST',f'/children/{profile_id}/consultation-requests',{'title':'Routine review request','date':today().isoformat(),'notes':'Synthetic request only'},session=parent,role='PATIENT',expected=201)
call('Doctor consultation requests','GET','/doctors/consultation-requests?page=1&per_page=25',session=session)
call('Doctor requests for connected child','GET',f'/children/{profile_id}/consultation-requests?page=1&per_page=25',session=session)
admin=login('admin')
vaccine=client.post('/api/v1/admin/vaccination/vaccines',headers=auth(admin),json={'code':'EXAMPLE','name_en':'Synthetic vaccine','category':'Government','protects_against':'Synthetic example only'}).json['vaccine']
schedule=client.post('/api/v1/admin/vaccination/schedules',headers=auth(admin),json={'vaccine_id':vaccine['id'],'schedule_type':'UIP','dose_code':'D1','dose_name':'Synthetic dose','version':'demo-v1','age_label':'Synthetic example only','age_unit':'years','age_start':6,'age_end':7,'route':'Other','source_url':'https://example.org/synthetic-guideline','source_reference':'Synthetic fixture, not a clinical guideline','effective_from':'2026-01-01'}).json['schedule'];schedule_id=schedule['id']
assert client.post(f'/api/v1/admin/vaccination/schedules/{schedule_id}/submit-review',headers=auth(admin),json={'reviewer_id':doctor_id}).status_code==200
call('Assigned doctor vaccination reviews','GET','/doctors/vaccination-reviews?page=1&per_page=25',session=session)
call('Doctor approves assigned review','POST',f'/doctors/vaccination-reviews/{schedule_id}',{'decision':'APPROVE','notes':'Synthetic fixture review, not a clinical approval of real patient care.','attestation':True},session=session)
call('Refresh doctor Bearer session','POST','/auth/refresh',{'refresh_token':session['refresh_token']})
call('Doctor active sessions','GET','/auth/sessions',session=session)
other=login()
with app.app_context():sid=decode_token(other['access_token'],'access')['sid']
call('Revoke another doctor session','DELETE','/auth/sessions/'+sid,session=session)
call('Doctor password change','POST','/auth/change-password',{'current_password':password,'new_password':'ChangedExample8!','confirm_password':'ChangedExample8!'},session=session);password='ChangedExample8!'
reset=call('Doctor forgot password','POST','/auth/forgot-password',{'email':'doctor@example.com'},expected=202)
with app.app_context():
    for item in db().scalars(select(OTPChallenge).where(OTPChallenge.user_id==doctor_id)).all():item.created_at=now()-timedelta(seconds=61)
    db().commit()
reset=call('Resend password reset OTP','POST','/auth/resend-otp',{'challenge_token':reset['challenge_token']})
call('Doctor reset password','POST','/auth/reset-password',{'challenge_token':reset['challenge_token'],'otp':code(reset['challenge_token']),'new_password':'ResetExample8!','confirm_password':'ResetExample8!'})
password='ResetExample8!';session=login();call('Doctor logout','POST','/auth/logout',{},session=session)
session=login();call('Doctor logout all devices','POST','/auth/logout-all',{},session=session)
ids={doctor_id:'11111111-1111-4111-8111-111111111111',patient_id:'22222222-2222-4222-8222-222222222222',profile_id:'33333333-3333-4333-8333-333333333333',report_id:'44444444-4444-4444-8444-444444444444',schedule_id:'55555555-5555-4555-8555-555555555555'}
def clean(value,key=''):
    if key in ('access_token','refresh_token','challenge_token','csrf_token'):return '{{'+key+'}}'
    if key=='otp':return '123456'
    if isinstance(value,dict):return {k:clean(v,k) for k,v in value.items()}
    if isinstance(value,list):return [clean(v,key) for v in value]
    if isinstance(value,str):
        if value.startswith('https://api.cloudinary.com/'):return 'https://api.cloudinary.com/v1_1/example-cloud/raw/download?SIGNED_PARAMETERS'
        for old,new in ids.items():value=value.replace(old,new)
    return value
examples=clean(examples)
notice='Synthetic examples captured from isolated SQLite. Credentials, tokens, IDs and links are examples, not live patient data. Scenarios have separate preconditions; do not run this file as one linear workflow.'
base='http://127.0.0.1:5001/api/v1'
(DOCS/'DOCTOR_API_EXAMPLES.json').write_text(json.dumps(dict(base_url=base,notice=notice,examples=examples),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Complete doctor APIs: request and output JSON','',notice,'','Base: `'+base+'`. Protected requests use `Authorization: Bearer DOCTOR_ACCESS_TOKEN`. PATIENT actions require the patient token. GET has no body. Refresh requires its refresh-token credential in JSON.','', 'Doctor login uses email/password; no doctor login-OTP endpoint exists. Email verification and password-reset OTP are separate. Cookie-mode login sets HttpOnly cookies and omits access/refresh tokens from JSON.','', '## API index','', '| # | Method | Endpoint | Auth | HTTP |','| --- | --- | --- | --- | --- |']
for n,item in enumerate(examples,1):lines.append(f"| {n} | {item['method']} | `{item['url'].replace(base,'')}` | {item['auth']} | {item['response_status']} |")
for n,item in enumerate(examples,1):
    lines+=['',f"## {n}. {item['name']}",'',f"`{item['method']} {item['url']}`",'',f"Authentication: **{item['auth']}**.",'','Request JSON:' if item['request_json'] is not None else 'Request body: **none**.']
    if item['request_json'] is not None:lines+=['','```json',json.dumps(item['request_json'],indent=2,ensure_ascii=False),'```']
    lines+=['',f"Output JSON - HTTP {item['response_status']}:",'','```json',json.dumps(item['response_json'],indent=2,ensure_ascii=False),'```']
lines+=['','## Access and workflow notes','','- Account referral and family-profile referral are separate. `/doctors/patients` lists account referrals; `/doctors/care-profiles` lists profile referrals.','- Doctor report endpoints read/download only. OCR/translation requires the patient owner; no doctor OCR endpoint exists.','- Consultation endpoints list requests. No doctor consultation accept/reject/book endpoint is implemented.','- Review decision may be APPROVE or REJECT. REJECT returns a schedule to DRAFT. Do not automate professional attestation from these synthetic examples. Admin publication is separate.','- `/auth/initial-password` is superadmin bootstrap, not a doctor flow. Password changes/reset revoke sessions; resend has a 60-second cooldown.','- Pagination: page >= 1, per_page 1-100. Errors: 401 invalid session, 403 role/account/CSRF restriction, 404 inaccessible record, 409 invalid state, 422 invalid fields, 429 cooldown/rate limit.','','```json','{"error":{"code":"forbidden","message":"Insufficient permissions"}}','```','']
(DOCS/'DOCTOR_ALL_APIS.md').write_text('\n'.join(lines),encoding='utf-8')
print('Exported',len(examples),'verified request/output examples')

# Importable Postman requests, with recorded synthetic response examples.
import re
collection={'info':{'name':'FamilyCare Doctor APIs and Referral','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json','description':notice},'variable':[{'key':'base_url','value':base}]+[{'key':key,'value':''} for key in ('doctor_access_token','patient_access_token','refresh_token','challenge_token','profile_id','report_id','schedule_id','session_id')],'item':[]}
for item in examples:
    endpoint=item['url'].replace(base,'{{base_url}}')
    for value,key in [('33333333-3333-4333-8333-333333333333','profile_id'),('44444444-4444-4444-8444-444444444444','report_id'),('55555555-5555-4555-8555-555555555555','schedule_id')]:endpoint=endpoint.replace(value,'{{'+key+'}}')
    if '/auth/sessions/' in endpoint:endpoint=re.sub(r'/auth/sessions/[^?]+','/auth/sessions/{{session_id}}',endpoint)
    request={'method':item['method'],'url':endpoint,'header':[{'key':'Content-Type','value':'application/json'}]}
    if item['auth'] in ('DOCTOR','PATIENT'):request['header'].append({'key':'Authorization','value':'Bearer {{'+('doctor_access_token' if item['auth']=='DOCTOR' else 'patient_access_token')+'}}'})
    if item['request_json'] is not None:request['body']={'mode':'raw','raw':json.dumps(item['request_json'],indent=2),'options':{'raw':{'language':'json'}}}
    example={'name':item['name'],'originalRequest':request,'status':'Example','code':item['response_status'],'header':[{'key':'Content-Type','value':'application/json'}],'body':json.dumps(item['response_json'],indent=2)}
    collection['item'].append({'name':item['name'],'request':request,'response':[example]})
(DOCS/'DOCTOR_API.postman_collection.json').write_text(json.dumps(collection,indent=2)+'\n',encoding='utf-8')
print('Postman collection exported')
