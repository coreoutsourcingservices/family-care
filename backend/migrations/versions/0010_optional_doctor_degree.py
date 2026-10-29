"""Compatibility revision for the deployed optional qualification schema.

The configured database already records this revision, but its source was absent
from main. Its nullable qualification column was inspected before restoring this
idempotent compatibility step. Existing database revision records are preserved.
"""
from alembic import op

revision = '0010_optional_doctor_degree'
down_revision = '0008_report_text'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('doctor_profiles', 'qualification', nullable=True, schema='familycare')


def downgrade():
    raise RuntimeError('Qualification downgrade requires explicit data validation')
