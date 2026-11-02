import pytest
from sqlalchemy import select
from conftest import create_account
from core.database import db
from core.models import User, DoctorProfile, ApprovalRequest, EmailNotification
from test_workflows import bearer


@pytest.mark.parametrize('kind,role', [('doctors','DOCTOR'),('patients','PATIENT')])
@pytest.mark.parametrize('decision', ['approve','reject'])
def test_separate_review_queues(app, client, kind, role, decision):
    create_account(app)
    applicant = create_account(app, role=role)
    with app.app_context():
        user = db().get(User, applicant)
        user.approval_status = 'PENDING_APPROVAL'
        if role == 'DOCTOR':
            db().add(DoctorProfile(user_id=applicant, qualification='MBBS', medical_registration_number='TEST-1', registering_council='Test Council'))
            db().add(ApprovalRequest(applicant_id=applicant, applicant_role=role))
        public_id = user.public_id
        db().commit()
    headers = bearer(client.post('/api/v1/superadmin/login', json={'username':'superadmin','password':'Password8!'}))
    root = '/api/v1/superadmin/approvals/'
    response = client.get(root+kind, headers=headers)
    assert response.status_code == 200 and response.json['total'] == 1
    other = 'patients' if kind == 'doctors' else 'doctors'
    assert client.get(root+other, headers=headers).json['total'] == 0
    assert client.post(root+kind+'/'+public_id+'/reject', json={'reason':''}, headers=headers).status_code == 422
    response = client.post(root+kind+'/'+public_id+'/'+decision, json={'reason':'Verification incomplete'}, headers=headers)
    assert response.status_code == 200
    assert response.json['user']['approval_status'] == ('APPROVED' if decision == 'approve' else 'REJECTED')
    assert client.get(root+kind, headers=headers).json['total'] == 0
    assert client.post(root+kind+'/'+public_id+'/'+decision, json={'reason':'Again'}, headers=headers).status_code == 409
    with app.app_context():
        review = db().scalar(select(ApprovalRequest).where(ApprovalRequest.applicant_id==applicant))
        assert review.reviewed_by and review.reviewed_at
        assert db().scalar(select(EmailNotification).where(EmailNotification.user_id==applicant)).template == role.lower()+'_'+('approved' if decision=='approve' else 'rejected')


def test_queue_requires_superadmin(app, client):
    create_account(app, role='ADMIN', email='admin@example.com')
    headers = bearer(client.post('/api/v1/admin/login', json={'email':'admin@example.com','password':'Password8!'}))
    assert client.get('/api/v1/superadmin/approvals/doctors', headers=headers).status_code == 403
    assert client.get('/api/v1/superadmin/approvals/patients').status_code == 401
