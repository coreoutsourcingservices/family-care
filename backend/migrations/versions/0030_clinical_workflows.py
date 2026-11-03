"""Confirmed consultation times, availability and issued prescriptions."""
from alembic import op
import sqlalchemy as sa
from core.models import DoctorPrescription,DoctorAvailability
revision='0030_clinical_workflows'
down_revision='0029_activity_retention'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('care_reports',sa.Column('title',sa.String(160)),schema='familycare')
    op.add_column('pregnancy_care',sa.Column('details',sa.JSON(),nullable=False,server_default='{}'),schema='familycare')
    for column in [sa.Column('confirmed_at',sa.DateTime()),sa.Column('duration_minutes',sa.Integer(),nullable=False,server_default='30'),sa.Column('version',sa.Integer(),nullable=False,server_default='1')]:
        op.add_column('doctor_consultations',column,schema='familycare')
    DoctorPrescription.__table__.create(op.get_bind(),checkfirst=True)
    DoctorAvailability.__table__.create(op.get_bind(),checkfirst=True)

def downgrade():
    raise RuntimeError('Clinical workflow history requires a reviewed downgrade')
