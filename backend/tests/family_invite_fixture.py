"""Synthetic browser fixture only: isolated SQLite, in-memory mail sink, no external writes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import jsonify
from app import create_app
from core.database import Base,db
from core.models import User,PatientProfile
from core.security import password_hasher
import services.family_invitations as invites

app=create_app(dict(TESTING=True,DATABASE_URL='sqlite://',JWT_SECRET_KEY='test-'+'a'*48,
    OTP_HMAC_SECRET='test-'+'b'*48,RATELIMIT_ENABLED=False,RATELIMIT_STORAGE_URI='memory://',
    COOKIE_SECURE=False,CORS_ORIGINS=['http://127.0.0.1:5173'],FAMILY_INVITE_FRONTEND_URL='http://127.0.0.1:5173'))
messages=[]
invites.send_mail=lambda email,subject,body,message_id:messages.append(dict(email=email,subject=subject,body=body))
with app.app_context():
    Base.metadata.create_all(app.extensions['database_engine'])
    owner=User(id='00000000-0000-4000-8000-000000000001',public_id='C_TEST_FAMILY',full_name='Example Family',
        email='family@example.com',password_hash=password_hasher.hash('FamilyPassword8!'),role='PATIENT',
        email_verified=True,approval_status='APPROVED',account_status='ACTIVE')
    db().add(owner);db().flush();db().add(PatientProfile(user_id=owner.id));db().commit()

@app.get('/__test/mail')
def mail_sink():return jsonify(items=messages)

if __name__=='__main__':
    from waitress import serve
    serve(app,host='127.0.0.1',port=5508,threads=1)
