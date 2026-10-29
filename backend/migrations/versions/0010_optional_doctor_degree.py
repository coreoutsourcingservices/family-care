"""Allow doctor signup without a degree; preserve approval and council checks."""
from alembic import op
import sqlalchemy as sa

revision = '0010_optional_doctor_degree'
down_revision = '0009_doctor_practice'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('doctor_profiles', 'qualification', existing_type=sa.String(200),
                    nullable=True, schema='familycare')


def downgrade():
    # Refuse a lossy downgrade rather than inventing qualifications for doctors.
    connection = op.get_bind()
    if connection.execute(sa.text('SELECT count(*) FROM familycare.doctor_profiles WHERE qualification IS NULL')).scalar():
        raise RuntimeError('Complete missing doctor qualifications before downgrading.')
    op.alter_column('doctor_profiles', 'qualification', existing_type=sa.String(200),
                    nullable=False, schema='familycare')
