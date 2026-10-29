"""Separate verified doctor signup from profile submission and review."""
from alembic import op
import sqlalchemy as sa

revision = '0011_doctor_onboarding'
down_revision = '0010_optional_doctor_degree'
branch_labels = None
depends_on = None


def upgrade():
    for name in ('qualification', 'medical_registration_number', 'registering_council'):
        op.alter_column('doctor_profiles', name, nullable=True, schema='familycare')
    op.add_column('doctor_profiles', sa.Column('address', sa.String(1000)), schema='familycare')
    op.add_column('doctor_profiles', sa.Column('clinic_address', sa.String(1000)), schema='familycare')
    op.add_column('doctor_profiles', sa.Column('years_of_experience', sa.Integer()), schema='familycare')
    connection = op.get_bind()
    for check in sa.inspect(connection).get_check_constraints('users', schema='familycare'):
        if 'approval_status' in check['sqltext']:
            op.drop_constraint(op.f(check['name']), 'users', type_='check', schema='familycare')
    op.create_check_constraint(op.f('ck_users_approval'), 'users',
        "approval_status IN ('PENDING_EMAIL_VERIFICATION','PROFILE_REQUIRED','PENDING_APPROVAL','APPROVED','REJECTED')", schema='familycare')


def downgrade():
    raise RuntimeError('Doctor onboarding downgrade requires explicit data migration')
