"""Daily doctor appointment windows with patient capacities."""
from alembic import op
from core.models import DoctorAppointmentSchedule, CapacityAppointment

revision = '0033_capacity_appointments'
down_revision = '0032_women_articles'
branch_labels = None
depends_on = None


def upgrade():
    DoctorAppointmentSchedule.__table__.create(op.get_bind(), checkfirst=True)
    CapacityAppointment.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError('Booked appointments require a reviewed archival migration')
