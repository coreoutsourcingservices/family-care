"""Patient-approved, report-scoped doctor handoffs."""
from alembic import op
from core.models import DoctorHandoff
revision = '0027_doctor_handoffs'
down_revision = '0026_pregnancy_care'
branch_labels = None
depends_on = None

def upgrade():
    DoctorHandoff.__table__.create(op.get_bind(), checkfirst=True)

def downgrade():
    raise RuntimeError('Doctor handoff consent history requires a reviewed downgrade')
