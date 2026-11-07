"""Explicit, idempotent synthetic fixtures for one approved doctor. Sends no emails."""
import argparse, secrets
from datetime import date,datetime,timedelta,timezone
from uuid import uuid5,NAMESPACE_URL
from zoneinfo import ZoneInfo
from flask import g
from sqlalchemy import select,func
from app import create_app
from core.database import db
from core.models import (User,CareProfile,ChildRecord,ChildRecordRevision,AdultRecord,AdultRecordRevision,
 WomenDiaryRecord,WomenAccessGrant,AdultTabGrant,DoctorPrescription,CareReport,
 DoctorConsultation,DoctorAppointmentSchedule,CapacityAppointment,now)
from core.security import password_hasher
from patient.child_routes import RecordInput
from patient.adult_routes import AdultInput
from services.prescriptions import Draft
from services.women_workspace import WomenRecordInput,TABS as WOMEN_TABS
from services.adult_workspace import TABS as ADULT_TABS
from services.repository import audit

LABEL='DEMO / SAMPLE ONLY. Fictional workspace preview; not medical advice or a real prescription.'

def identifier(doctor_id,key):return str(uuid5(NAMESPACE_URL,'familycare:doctor-demo-v1:'+doctor_id+':'+key))

def pdf(lines):
    text='BT /F1 13 Tf 45 780 Td '+ ' '.join(('('+line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')+') Tj 0 -26 Td') for line in lines)+' ET'
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',b'<< /Length '+str(len(text.encode())).encode()+b' >>\nstream\n'+text.encode()+b'\nendstream',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    result=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objects,1):offsets.append(len(result));result+=str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref=len(result);result+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{o:010d} 00000 n \n'.encode() for o in offsets[1:])
    return result+f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()

def seed(email):
 app=create_app();today=datetime.now(ZoneInfo('Asia/Kolkata')).date();count={}
 with app.test_request_context():
  doctor=db().scalar(select(User).where(User.email==email,User.role=='DOCTOR'))
  if not doctor or doctor.full_name!='gqwyrew' or doctor.approval_status!='APPROVED' or doctor.account_status!='ACTIVE':raise RuntimeError('Expected approved gqwyrew doctor account')
  g.user=doctor
  def add(model,key,**values):
   pk=identifier(doctor.id,key);row=db().get(model,pk)
   if row:return row
   row=model(id=pk,**values);db().add(row);db().flush();count[model.__name__]=count.get(model.__name__,0)+1;return row
  schedule=db().get(DoctorAppointmentSchedule,doctor.id)
  if not schedule:
   schedule=DoctorAppointmentSchedule(doctor_id=doctor.id,version=1,windows=[{'id':identifier(doctor.id,'window-am'),'start':'09:00','end':'12:00','capacity':50,'days':list(range(7))},{'id':identifier(doctor.id,'window-pm'),'start':'14:00','end':'17:00','capacity':50,'days':list(range(7))}]);db().add(schedule);db().flush()
  fixtures=[('ama','Ama','child',date(2018,6,15),'Male'),('pk','PK','child',date(2019,3,20),'Male'),('saif','Saif','adult',date(1991,9,12),'Male'),('riya','Riya','women',date(1998,11,4),'Female')]
  profile_ids=[]
  for index,(key,name,module,dob,gender) in enumerate(fixtures):
   owner=add(User,key+'-owner',public_id=None,full_name=name+' DEMO account',email=key+'.'+doctor.public_id.lower()+'@familycare-demo.invalid',password_hash=password_hasher.hash(secrets.token_urlsafe(40)),role='PATIENT',email_verified=True,approval_status='APPROVED',account_status='ACTIVE',must_change_password=True)
   profile=add(CareProfile,key+'-profile',owner_id=owner.id,module=module,name=name+' (DEMO)',dob=dob,gender=gender,profile_type='member' if module=='child' else 'self',guardian_name='DEMO guardian' if module=='child' else '',guardian_contact='',emergency_contacts=[],referred_doctor_id=doctor.id,created_at=now()-timedelta(days=120-index*20))
   if profile.referred_doctor_id!=doctor.id or profile.owner_id!=owner.id:raise RuntimeError('Fixture ownership changed; refusing overwrite')
   profile_ids.append(profile.id)
   if module in ('adult','women'):
    model,tabs=(AdultTabGrant,ADULT_TABS) if module=='adult' else (WomenAccessGrant,WOMEN_TABS)
    add(model,key+'-grant',profile_id=profile.id,recipient_id=doctor.id,granted_by=owner.id,permissions={t:'edit' for t in tabs},starts_at=None,expires_at=None)
   if module=='child':
    for i in range(4):
     stamp=today-timedelta(days=90-i*25)
     for kind,extra in [('growth',{'weight':str(21+index+i*.4),'height':str(119+index+i)}),('nutrition',{'meal':'Lunch','notes':LABEL+' Example: rice, vegetables and fruit.'}),('care',{'notes':LABEL+' Example daily activity note.'})]:
      value=RecordInput(title=f'DEMO - {name} {kind} {i+1}',date=stamp,**extra).model_dump(mode='json',exclude={'version'});value.update(source_role='DOCTOR',author_id=doctor.id,author_name=doctor.full_name);value['notes']=value.get('notes') or LABEL
      record=add(ChildRecord,f'{key}-{kind}-{i}',profile_id=profile.id,kind=kind,data=value,created_at=datetime.combine(stamp,datetime.min.time()))
      add(ChildRecordRevision,f'{key}-{kind}-{i}-revision',record_id=record.id,actor_id=doctor.id,action='created',data=value)
    for i in range(2):
     value=RecordInput(title=f'DEMO - {name} sample care follow-up {i+1}',date=today+timedelta(days=i),status='REQUESTED',notes=LABEL).model_dump(mode='json',exclude={'version'});value.update(source_role='PARENT',author_id=owner.id)
     add(ChildRecord,f'{key}-request-{i}',profile_id=profile.id,kind='consultation_request',data=value)
    value=RecordInput(title='DEMO - Unscheduled vaccination example',date=today-timedelta(days=14),status='Completed',notes=LABEL,provider='DEMO clinic').model_dump(mode='json',exclude={'version'});value.update(source_role='DOCTOR',author_id=doctor.id,author_name=doctor.full_name)
    add(ChildRecord,key+'-vaccination',profile_id=profile.id,kind='vaccination',data=value)
   elif module=='adult':
    for i in range(4):
     stamp=today-timedelta(days=60-i*18)
     for kind,extra in [('bp',{'systolic':118+i,'diastolic':76+i,'pulse':70+i}),('glucose',{'glucose':91+i*2,'units':'mg/dL','reading_context':'Fasting'}),('lipids',{'total':176+i*3,'ldl':96+i,'hdl':52+i,'triglycerides':118+i*3}),('lifestyle',{'minutes':20+i*5,'context':'Walking'})]:
      value=AdultInput(kind=kind,title=f'DEMO - {name} {kind} {i+1}',date=stamp,notes=LABEL,**extra).model_dump(mode='json',exclude={'version'});record=add(AdultRecord,f'{key}-{kind}-{i}',profile_id=profile.id,kind=kind,data=value,created_at=datetime.combine(stamp,datetime.min.time()));add(AdultRecordRevision,f'{key}-{kind}-{i}-revision',record_id=record.id,actor_id=owner.id,action='created',data=value)
   else:
    for i,section in enumerate(['health','cycle','symptoms','nutrition','screening']):
     value=WomenRecordInput(section=section,data={'title':f'DEMO - {name} {section}','date':(today-timedelta(days=15-i*3)).isoformat(),'notes':LABEL,'status':'Completed'}).data
     add(WomenDiaryRecord,key+'-'+section,profile_id=profile.id,section=section,data=value,updated_by=owner.id,version=1)
   draft=Draft(medicines=[dict(name='DEMO sample item',strength='Fictional',dose='DEMO only',frequency='Not for use',duration='Sample only',instructions='Not a real medicine or prescription.')],instructions=LABEL,follow_up=today+timedelta(days=7))
   add(DoctorPrescription,key+'-rx',profile_id=profile.id,doctor_id=doctor.id,status='DRAFT',version=1,data=draft.model_dump(mode='json',exclude={'version'}))
   for i,category in enumerate(['Lab tests','Scans']):
    content=pdf(['FAMILYCARE - DEMO / SAMPLE ONLY',name+' (DEMO)',category+' - fictional document','Date: '+(today-timedelta(days=i+1)).isoformat(),'No clinical diagnosis or treatment is provided.','For testing report viewing and downloading only.'])
    add(CareReport,key+'-report-'+str(i),profile_id=profile.id,title='DEMO - '+name+' '+category,name='DEMO-'+name+'-'+('lab' if i==0 else 'scan')+'.pdf',category=category,category_reviewed=True,content_type='application/pdf',content=content,storage_provider='database',size_bytes=len(content),created_at=now()-timedelta(days=i+1))
   if module=='child':
    for i in range(2):
     report_id=identifier(doctor.id,key+'-report-'+str(i))
     data=RecordInput(title='DEMO - Shared report attachment '+str(i+1),date=today-timedelta(days=i+1),notes=LABEL+' Supporting demo document shared for viewing.').model_dump(mode='json',exclude={'version'})
     data.update(source_role='PARENT',author_id=owner.id,source_report_id=report_id)
     record=add(ChildRecord,key+'-report-attachment-'+str(i),profile_id=profile.id,kind='care',data=data)
     add(ChildRecordRevision,key+'-report-attachment-revision-'+str(i),record_id=record.id,actor_id=owner.id,action='created',data=data)
   for i in range(2):
    planned=datetime.combine(today+timedelta(days=i),datetime.min.time()).replace(hour=15+index//2,minute=(index%2)*30,tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc).replace(tzinfo=None)
    add(DoctorConsultation,f'{key}-visit-{i}',profile_id=profile.id,patient_id=owner.id,doctor_id=doctor.id,concern='DEMO - '+name+' sample consultation',notes=LABEL,requested_at=planned,confirmed_at=planned if i==0 else None,status='CONFIRMED' if i==0 else 'REQUESTED',duration_minutes=30,version=1)
   booking_id=identifier(doctor.id,key+'-booking')
   if not db().get(CapacityAppointment,booking_id):
    for delta in range(1,31):
     booking_day=today+timedelta(days=delta)
     found=False
     for w in schedule.windows:
      used=db().scalar(select(func.count()).select_from(CapacityAppointment).where(CapacityAppointment.doctor_id==doctor.id,CapacityAppointment.window_id==w['id'],CapacityAppointment.appointment_date==booking_day,CapacityAppointment.status.in_(['BOOKED','COMPLETED'])))
      if booking_day.weekday() in w['days'] and used<w['capacity']:
       add(CapacityAppointment,key+'-booking',doctor_id=doctor.id,patient_id=owner.id,profile_id=profile.id,window_id=w['id'],request_id=identifier(doctor.id,key+'-booking-request'),appointment_date=booking_day,start_time=w['start'],end_time=w['end'],status='BOOKED',email_id=None);found=True;break
     if found:break
    else:raise RuntimeError('No available appointment window; existing schedule was preserved')
   audit('doctor_demo_fixture_seeded',profile.owner_id,doctor.id)
  db().commit()
  print({'doctor':doctor.full_name,'public_id':doctor.public_id,'added':count,'demo_profiles':profile_ids,'outbound_emails_created':0},flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--doctor-email',required=True)
 try:seed(parser.parse_args().doctor_email)
 except Exception as exc:
  detail=getattr(getattr(getattr(exc,'orig',None),'diag',None),'message_primary',None)
  print({'error_type':type(exc).__name__,'detail':detail or 'Demo seed failed; existing account data was preserved.'},flush=True);raise SystemExit(1)
