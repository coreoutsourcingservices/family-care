"""Isolated in-memory API for admin/tests/smoke.mjs. Never uses the configured database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from core.database import Base, db
from core.models import User, DoctorProfile, PatientProfile, ApprovalRequest, uid
from core.security import password_hasher

app = create_app(dict(TESTING=True, DATABASE_URL='sqlite://', APP_ENV='development',
    JWT_SECRET_KEY='frontend-smoke-jwt-' + 'a'*48, OTP_HMAC_SECRET='frontend-smoke-otp-' + 'b'*48,
    RATELIMIT_ENABLED=False, RATELIMIT_STORAGE_URI='memory://', COOKIE_SECURE=False,
    CORS_ORIGINS=['http://localhost:3006', 'http://127.0.0.1:3006']))
# No SMTP calls in isolated integration tests.
import services.signup
services.signup.send_mail = lambda *args, **kwargs: None
Base.metadata.create_all(app.extensions['database_engine'])
with app.app_context():
    for role, public_id, email, approval in [
        ('ADMIN', 'A_TEST', 'admin@example.com', 'APPROVED'),
        ('SUPERADMIN', 'superadmin', 'super@example.com', 'APPROVED'),
        ('PATIENT', 'C_TEST', 'patient@example.com', 'APPROVED'),
        ('DOCTOR', 'D_TEST', 'doctor@example.com', 'PENDING_APPROVAL')]:
        user = User(id=uid(), public_id=public_id, username='superadmin' if role == 'SUPERADMIN' else None,
                    full_name='Test '+role.title(), email=email, role=role,
                    password_hash=password_hasher.hash('SmokePassword8!'),
                    email_verified=True, approval_status=approval)
        db().add(user)
        db().flush()
        if role == 'PATIENT':
            db().add(PatientProfile(user_id=user.id))
        if role == 'DOCTOR':
            db().add(DoctorProfile(user_id=user.id, qualification='MBBS',
                                  medical_registration_number='TEST-1', registering_council='Test Council'))
            db().add(ApprovalRequest(applicant_id=user.id, applicant_role=role))
    db().commit()

if __name__ == '__main__':
    from waitress import serve
    # In-memory SQLite uses a single connection; serialize fixture requests.
    # Production PostgreSQL continues to use its normal concurrent connection pool.
    serve(app, host='127.0.0.1', port=5501, threads=1)
