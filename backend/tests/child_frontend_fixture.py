"""Isolated child-care browser fixture. No Supabase writes or SMTP calls."""
from datetime import date
from frontend_fixture import app
from sqlalchemy import select
from core.database import db
from core.models import User, CareProfile

app.config['CORS_ORIGINS'].append('http://127.0.0.1:5175')
# CORS was initialized from the original list; browser fixture uses a Vite proxy.
with app.app_context():
    owner = db().scalar(select(User).where(User.email == 'patient@example.com'))
    doctor = db().scalar(select(User).where(User.email == 'doctor@example.com'))
    doctor.approval_status = 'APPROVED'
    db().add(CareProfile(owner_id=owner.id, module='child', name='Demo Child',
                         dob=date(2020, 3, 1), profile_type='member', referred_doctor_id=doctor.id))
    db().commit()

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='127.0.0.1', port=5501, threads=1)
