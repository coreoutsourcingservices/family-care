"""Isolated temporary SQLite browser QA server; never uses the real database."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import date, timedelta
from app import create_app
from core.database import Base, db
from core.models import User, PatientProfile, DoctorProfile, CareProfile, FamilyInvitation, CareReport, now
from core.security import password_hasher

qa_directory=tempfile.TemporaryDirectory(prefix='familycare-women-qa-')
qa_url='sqlite:///'+(Path(qa_directory.name)/'qa.sqlite').as_posix()
app = create_app(dict(TESTING=True, DATABASE_URL=qa_url, APP_ENV='development',
    JWT_SECRET_KEY='isolated-browser-test-'+'a'*48, OTP_HMAC_SECRET='isolated-browser-test-'+'b'*48,
    RATELIMIT_ENABLED=False, COOKIE_SECURE=False, RATELIMIT_STORAGE_URI='memory://',
    CORS_ORIGINS=['http://127.0.0.1:5176'], SESSION_ALLOWED_ORIGINS=['http://127.0.0.1:5176'],
    CLOUDINARY_CLOUD_NAME='', CLOUDINARY_API_KEY='', CLOUDINARY_API_SECRET='', CLINIC_GEOCODING_ENABLED=False))
Base.metadata.create_all(app.extensions['database_engine'])
with app.extensions['database_engine'].connect() as connection:
    connection.exec_driver_sql('PRAGMA foreign_keys=ON')
owner='11111111-1111-4111-8111-111111111111'
member='22222222-2222-4222-8222-222222222222'
doctor='33333333-3333-4333-8333-333333333333'
profile='44444444-4444-4444-8444-444444444444'
member_profile='55555555-5555-4555-8555-555555555555'
with app.app_context():
    for id, role, email, name in [(owner,'PATIENT','owner@example.com','QA Woman'),
        (member,'PATIENT','family@example.com','QA Family'),(doctor,'DOCTOR','doctor@example.com','Dr QA')]:
        db().add(User(id=id, public_id=('D' if role=='DOCTOR' else 'C')+id[:8],role=role,
            full_name=name,email=email,password_hash=password_hasher.hash('BrowserTest8!'),
            email_verified=True,approval_status='APPROVED',account_status='ACTIVE'))
    db().flush()
    db().add_all([PatientProfile(user_id=owner),PatientProfile(user_id=member),
        DoctorProfile(user_id=doctor,qualification='MBBS',medical_registration_number='BROWSER-QA-ONLY',registering_council='Test')])
    db().add_all([CareProfile(id=profile,owner_id=owner,module='women',profile_type='self',name='QA Woman',dob=date(1990,1,1),
        referred_doctor_id=doctor,guardian_contact='',guardian_name='',emergency_contacts=[]),
        CareProfile(id=member_profile,owner_id=owner,module='adult',profile_type='member',name='QA Family',dob=date(1989,1,1),
        guardian_contact='',guardian_name='',emergency_contacts=[])])
    db().flush()
    db().add(FamilyInvitation(owner_id=owner,member_id=member,profile_id=member_profile,token_hash='browser-qa-only',
        email='family@example.com',full_name='QA Family',module='adult',relationship='Partner',accepted_at=now(),expires_at=now()+timedelta(days=1)))
    db().add(CareReport(profile_id=profile,name='QA-report.pdf',content_type='application/pdf',content=b'%PDF-1.7\nSynthetic QA report',storage_provider='database'))
    db().commit()
if __name__=='__main__':
    from scripts.notification_socket import start_background
    # Separate connections prevent the gateway's concurrent reads from rolling back API writes.
    start_background(create_app(dict(app.config)),port=5004)
    app.run(host='127.0.0.1',port=5003,threaded=False,use_reloader=False)
