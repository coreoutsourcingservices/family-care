"""Adult tab permissions, access history and real consultation ratings."""
from alembic import op
from sqlalchemy import Column, DateTime, inspect
from core.models import AdultTabGrant, HealthAccessEvent, DoctorConsultation, DoctorReview
revision='0024_health_sharing_consultation'
down_revision='0023_merge_notes_women'
branch_labels=None
depends_on=None


def upgrade():
    bind=op.get_bind()
    if 'starts_at' not in {c['name'] for c in inspect(bind).get_columns('women_access_grants',schema='familycare')}:
        op.add_column('women_access_grants',Column('starts_at',DateTime),schema='familycare')
    for model in (AdultTabGrant,HealthAccessEvent,DoctorConsultation,DoctorReview):
        model.__table__.create(bind,checkfirst=True)


def downgrade():
    raise RuntimeError('Consent, consultation and review history require a reviewed downgrade')
