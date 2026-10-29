"""Store doctor-owned practice details without changing signup/approval identity."""
from alembic import op
from core.models import DoctorPracticeProfile
revision='0009_doctor_practice'
down_revision='0008_report_text'
branch_labels=None
depends_on=None

def upgrade():
    DoctorPracticeProfile.__table__.create(op.get_bind(),checkfirst=True)
    if op.get_bind().dialect.name=='postgresql':
        op.execute('ALTER TABLE familycare.doctor_practice_profiles ENABLE ROW LEVEL SECURITY')
        op.execute('REVOKE ALL ON familycare.doctor_practice_profiles FROM anon, authenticated')

def downgrade():
    DoctorPracticeProfile.__table__.drop(op.get_bind())
