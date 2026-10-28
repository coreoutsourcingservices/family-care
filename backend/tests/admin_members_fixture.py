"""Synthetic family data for admin directory browser checks, in-memory only."""
from datetime import date
from sqlalchemy import select
from frontend_fixture import app
from core.database import db
from core.models import User, CareProfile

with app.app_context():
    owner = db().scalar(select(User).where(User.email == 'patient@example.com'))
    for name,module,kind,dob in [
        ('Parent self','adult','self',date(1990,1,1)),
        ('Aarav Kumar','child','member',date(2020,3,1)),
        ('Mira Kumar','child','member',date(2022,5,2)),
        ('Anaya Kumar','women','member',date(1995,4,3)),
    ]:
        db().add(CareProfile(owner_id=owner.id,name=name,module=module,profile_type=kind,dob=dob,
                            guardian_contact='+919876543210',emergency_contacts=[{'name':'Parent','mobile_number':'+919876543210'}]))
    db().commit()

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='127.0.0.1', port=5501, threads=1)
