"""Isolated browser fixture: no real patient data or email delivery."""
from datetime import date
from family_invite_fixture import app
from core.database import db
from core.models import User,DoctorProfile,CareProfile
from core.security import password_hasher

with app.app_context():
    doctor=User(id='00000000-0000-4000-8000-000000000002',public_id='D_TEST_GUIDE',full_name='Example Doctor',
        email='doctor@example.com',password_hash=password_hasher.hash('DoctorPassword8!'),role='DOCTOR',
        email_verified=True,approval_status='APPROVED',account_status='ACTIVE')
    db().add(doctor);db().flush()
    db().add(DoctorProfile(user_id=doctor.id,qualification='MBBS',medical_registration_number='GUIDE-TEST',
        registering_council='Synthetic Council',verification_status='APPROVED'))
    db().add(CareProfile(id='00000000-0000-4000-8000-000000000010',owner_id='00000000-0000-4000-8000-000000000001',
        module='child',profile_type='member',name='Example Child',dob=date(2026,2,28),referred_doctor_id=doctor.id))
    db().commit()

if __name__=='__main__':
    from waitress import serve
    serve(app,host='127.0.0.1',port=5509,threads=1)
