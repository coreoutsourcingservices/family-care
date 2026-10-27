"""Add stable doctor referral IDs and optional patient connections."""
from alembic import op
import sqlalchemy as sa
from core.referrals import make_referral_id

revision = '0003_doctor_referrals'
down_revision = '0002_care_profiles'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('doctor_profiles', sa.Column('referral_id', sa.String(160)), schema='familycare')
    connection = op.get_bind()
    rows = connection.execute(sa.text('SELECT u.id, u.full_name, u.public_id FROM familycare.users u '
                                     'JOIN familycare.doctor_profiles d ON d.user_id = u.id')).all()
    for row in rows:
        connection.execute(sa.text('UPDATE familycare.doctor_profiles SET referral_id = :referral WHERE user_id = :id'),
                           dict(referral=make_referral_id(row.full_name, row.public_id), id=row.id))
    op.alter_column('doctor_profiles', 'referral_id', nullable=False, schema='familycare')
    op.create_unique_constraint('uq_doctor_profiles_referral_id', 'doctor_profiles', ['referral_id'], schema='familycare')
    op.add_column('patient_profiles', sa.Column('referred_by_doctor_id', sa.Uuid()), schema='familycare')
    op.add_column('patient_profiles', sa.Column('referred_at', sa.DateTime()), schema='familycare')
    op.create_foreign_key('fk_patient_profiles_referred_by_doctor_id_doctor_profiles', 'patient_profiles',
                         'doctor_profiles', ['referred_by_doctor_id'], ['user_id'],
                         source_schema='familycare', referent_schema='familycare', ondelete='SET NULL')
    op.create_index('ix_patient_profiles_referred_by_doctor_id', 'patient_profiles', ['referred_by_doctor_id'], schema='familycare')


def downgrade():
    raise RuntimeError('Referral data downgrade is destructive; restore a reviewed backup instead.')
