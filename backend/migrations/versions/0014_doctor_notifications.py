"""Doctor notification inbox and private Web Push delivery queue."""
from alembic import op
import sqlalchemy as sa

revision = '0014_doctor_notifications'
down_revision = '0013_doctor_onboarding_images'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('doctor_notifications',
        sa.Column('id', sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column('user_id', sa.Uuid(as_uuid=False), sa.ForeignKey('familycare.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_key', sa.String(200), nullable=False), sa.Column('kind', sa.String(40), nullable=False),
        sa.Column('title', sa.String(160), nullable=False), sa.Column('body', sa.String(300), nullable=False),
        sa.Column('path', sa.String(160), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime()), sa.UniqueConstraint('user_id', 'event_key'), schema='familycare')
    op.create_index('ix_doctor_notifications_user_id', 'doctor_notifications', ['user_id'], schema='familycare')
    op.create_index('ix_doctor_notifications_created_at', 'doctor_notifications', ['created_at'], schema='familycare')
    op.create_table('doctor_push_subscriptions',
        sa.Column('id', sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column('user_id', sa.Uuid(as_uuid=False), sa.ForeignKey('familycare.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False), sa.Column('endpoint_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('keys', sa.JSON(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False), schema='familycare')
    op.create_index('ix_doctor_push_subscriptions_user_id', 'doctor_push_subscriptions', ['user_id'], schema='familycare')
    op.create_table('doctor_push_deliveries',
        sa.Column('id', sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column('notification_id', sa.Uuid(as_uuid=False), sa.ForeignKey('familycare.doctor_notifications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subscription_id', sa.Uuid(as_uuid=False), sa.ForeignKey('familycare.doctor_push_subscriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False), sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('next_attempt_at', sa.DateTime(), nullable=False), sa.UniqueConstraint('notification_id', 'subscription_id'), schema='familycare')
    op.create_index('ix_doctor_push_deliveries_status', 'doctor_push_deliveries', ['status'], schema='familycare')
    op.create_index('ix_doctor_push_deliveries_next_attempt_at', 'doctor_push_deliveries', ['next_attempt_at'], schema='familycare')


def downgrade():
    raise RuntimeError('Notification history removal requires a reviewed data migration')
