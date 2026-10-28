"""Private report OCR and translation results."""
from alembic import op
from core.models import ReportText
revision='0008_report_text'
down_revision='0007_vaccination_management'
branch_labels=None
depends_on=None

def upgrade():
    ReportText.__table__.create(op.get_bind(),checkfirst=True)
    if op.get_bind().dialect.name=='postgresql':
        op.execute('ALTER TABLE familycare.report_texts ENABLE ROW LEVEL SECURITY')
        op.execute('REVOKE ALL ON familycare.report_texts FROM anon, authenticated')

def downgrade():
    ReportText.__table__.drop(op.get_bind())
