"""Account-backed child care records and in-app reminder preferences."""
from alembic import op
from core.models import ChildRecord, ChildRecordRevision, ChildPreferences

revision = '0006_child_records'
down_revision = '0005_profile_public_ids'
branch_labels = None
depends_on = None


def upgrade():
    for model in (ChildRecord, ChildRecordRevision, ChildPreferences):
        model.__table__.create(op.get_bind(), checkfirst=True)
    # Private medical data is accessed only through authenticated Flask routes.
    if op.get_bind().dialect.name == 'postgresql':
        for table in ('child_records', 'child_record_revisions', 'child_preferences'):
            op.execute(f'ALTER TABLE familycare.{table} ENABLE ROW LEVEL SECURITY')
            op.execute(f'REVOKE ALL ON familycare.{table} FROM anon, authenticated')


def downgrade():
    for model in (ChildRecordRevision, ChildPreferences, ChildRecord):
        model.__table__.drop(op.get_bind())
