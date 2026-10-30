"""Adult health logs and edit history."""
from alembic import op
import sqlalchemy as sa
revision='0015_adult_records'
down_revision='0014_doctor_notifications'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('adult_records',sa.Column('id',sa.Uuid(as_uuid=False),primary_key=True),sa.Column('profile_id',sa.Uuid(as_uuid=False),sa.ForeignKey('familycare.care_profiles.id',ondelete='CASCADE'),nullable=False),sa.Column('kind',sa.String(32),nullable=False),sa.Column('data',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('updated_at',sa.DateTime(),nullable=False),sa.Column('deleted_at',sa.DateTime()),schema='familycare')
    op.create_index('ix_adult_records_profile_id','adult_records',['profile_id'],schema='familycare')
    op.create_table('adult_record_revisions',sa.Column('id',sa.Uuid(as_uuid=False),primary_key=True),sa.Column('record_id',sa.Uuid(as_uuid=False),sa.ForeignKey('familycare.adult_records.id',ondelete='CASCADE'),nullable=False),sa.Column('actor_id',sa.Uuid(as_uuid=False),sa.ForeignKey('familycare.users.id'),nullable=False),sa.Column('action',sa.String(12),nullable=False),sa.Column('data',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False),schema='familycare')
    op.create_index('ix_adult_record_revisions_record_id','adult_record_revisions',['record_id'],schema='familycare')

def downgrade():
    raise RuntimeError('Health record removal requires a reviewed data migration')
