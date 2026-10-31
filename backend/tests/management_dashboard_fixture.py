"""Synthetic superadmin preview fixture. No real accounts, SMTP or medical content."""
from datetime import datetime,date
from sqlalchemy import select
from frontend_fixture import app
from core.database import db
from core.models import User,PatientProfile,DoctorProfile,ApprovalRequest,CareProfile,ChildRecord,AuditLog,uid
from core.security import password_hasher

with app.app_context():
    superuser=db().scalar(select(User).where(User.role=='SUPERADMIN'));superuser.full_name='Super Admin'
    existing=db().scalar(select(User).where(User.role=='ADMIN'));existing.full_name='Example Administrator'
    month=date.today().year*12+date.today().month-1
    owner=db().scalar(select(User).where(User.role=='PATIENT'))
    doctor=db().scalar(select(User).where(User.role=='DOCTOR'))
    for i,(name,role) in enumerate([('Anita Singh','PATIENT'),('Ravi Verma','PATIENT'),('Priya Shah','PATIENT'),('Neha Sharma','DOCTOR'),('Amit Patel','DOCTOR'),('Suman Reddy','DOCTOR'),('Rahul Mehta','ADMIN'),('Vikash Kumar','ADMIN')]):
        y,m=divmod(month-(7-i)//2,12)
        user=User(id=uid(),public_id=role[0]+f'_PREVIEW_{i}',full_name=name,email=f'preview{i}@example.com',role=role,
            password_hash=password_hasher.hash('PreviewPassword8!'),email_verified=True,
            approval_status='PENDING_APPROVAL' if i>=6 or i==5 else 'APPROVED',created_at=datetime(y,m+1,min(20,i+1)))
        db().add(user);db().flush()
        if role=='PATIENT':db().add(PatientProfile(user_id=user.id))
        if role=='DOCTOR':db().add(DoctorProfile(user_id=user.id,qualification='MBBS',medical_registration_number='PREVIEW-'+str(i),registering_council='Preview Council'))
        if role in ('DOCTOR','ADMIN'):db().add(ApprovalRequest(applicant_id=user.id,applicant_role=role,status='PENDING' if user.approval_status=='PENDING_APPROVAL' else 'APPROVED'))
    for i in range(6):
        profile=CareProfile(id=uid(),owner_id=owner.id,module='child',name=f'Example Child {i+1}',dob=date(2020+i%5,2,10),referred_doctor_id=doctor.id)
        db().add(profile);db().flush()
        db().add(ChildRecord(profile_id=profile.id,kind='growth' if i%2 else 'nutrition',data={'title':'Synthetic care record'}))
    for i,action in enumerate(['registered','care_profile_created','growth_nutrition_activated','approval_approved','registered']):
        db().add(AuditLog(action=action,actor_id=superuser.id,target_id=owner.id))
    db().commit()

if __name__=='__main__':
    from waitress import serve
    serve(app,host='127.0.0.1',port=5511,threads=1)
