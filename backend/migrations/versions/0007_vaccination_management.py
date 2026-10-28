"""Versioned, medically reviewed vaccination definitions and private preferences."""
from alembic import op
from core.models import Vaccine, VaccineSchedule, VaccineAudit, ChildVaccinationContext, VaccineReminderDelivery

revision = '0007_vaccination_management'
down_revision = '0006_child_records'
branch_labels = None
depends_on = None
MODELS = (Vaccine, VaccineSchedule, VaccineAudit, ChildVaccinationContext, VaccineReminderDelivery)


def upgrade():
    for model in MODELS:
        model.__table__.create(op.get_bind(), checkfirst=True)
    if op.get_bind().dialect.name == 'postgresql':
        for model in MODELS:
            table = model.__tablename__
            op.execute(f'ALTER TABLE familycare.{table} ENABLE ROW LEVEL SECURITY')
            op.execute(f'REVOKE ALL ON familycare.{table} FROM anon, authenticated')


def downgrade():
    for model in reversed(MODELS):
        model.__table__.drop(op.get_bind())
