"""Vaccination UI tests: synthetic data, isolated SQLite and mocked private file store."""
from child_frontend_fixture import app
from core.database import db
from core.models import DoctorProfile
from sqlalchemy import select
import services.care_uploads
with app.app_context():
    for profile in db().scalars(select(DoctorProfile)).all():profile.verification_status='APPROVED'
    db().commit()
app.config.update(CLOUDINARY_CLOUD_NAME='test-cloud',CLOUDINARY_API_KEY='test-key',CLOUDINARY_API_SECRET='test-secret')
def fake_upload(stream,**options):
    return dict(public_id=options['public_id'],type=options['type'],resource_type=options['resource_type'],asset_id='test-asset',secure_url='https://res.cloudinary.com/test-cloud/raw/authenticated/test.pdf',format='pdf')
services.care_uploads.cloudinary.uploader.upload=fake_upload
if __name__=='__main__':
    from waitress import serve
    serve(app,host='127.0.0.1',port=5501,threads=1)
