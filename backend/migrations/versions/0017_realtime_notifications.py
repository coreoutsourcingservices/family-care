"""Account-scoped web/mobile notification inbox."""
from alembic import op
import sqlalchemy as sa
revision='0017_realtime_notifications'
down_revision='0016_child_profile_controls'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('app_notifications',sa.Column('id',sa.Integer(),primary_key=True,autoincrement=True),sa.Column('user_id',sa.Uuid(as_uuid=False),sa.ForeignKey('familycare.users.id',ondelete='CASCADE'),nullable=False),sa.Column('kind',sa.String(50),nullable=False),sa.Column('title',sa.String(160),nullable=False),sa.Column('body',sa.String(300),nullable=False),sa.Column('data',sa.JSON(),nullable=False),sa.Column('event_key',sa.String(200)),sa.Column('created_at',sa.DateTime(),nullable=False),sa.Column('read_at',sa.DateTime()),sa.UniqueConstraint('user_id','event_key'),schema='familycare')
    op.create_index('ix_app_notifications_user_id','app_notifications',['user_id'],schema='familycare')

def downgrade():
    raise RuntimeError('Notification history requires a reviewed data migration')
