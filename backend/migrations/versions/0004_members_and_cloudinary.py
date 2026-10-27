"""Adopt existing care tables, adding member/parent relationships and Cloudinary metadata."""
from alembic import op
import sqlalchemy as sa

revision = '0004_members_cloudinary'
down_revision = '0003_doctor_referrals'
branch_labels = None
depends_on = None


def upgrade():
    tables = sa.inspect(op.get_bind()).get_table_names(schema='familycare')
    if 'care_profiles' not in tables:
        op.create_table('care_profiles',
            sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('owner_id', sa.Uuid(), sa.ForeignKey('familycare.users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('module', sa.String(10), nullable=False),
            sa.Column('name', sa.String(120), nullable=False),
            sa.Column('dob', sa.Date(), nullable=False),
            sa.Column('guardian_contact', sa.String(20), nullable=False),
            sa.Column('emergency_contacts', sa.JSON(), nullable=False),
            sa.Column('referred_doctor_id', sa.Uuid(), sa.ForeignKey('familycare.users.id')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.CheckConstraint("module IN ('child','women','adult')", name=op.f('ck_care_profiles_module')),
            schema='familycare')
    op.add_column('care_profiles', sa.Column('profile_type', sa.String(10), nullable=False, server_default='member'), schema='familycare')
    op.add_column('care_profiles', sa.Column('parent_profile_id', sa.Uuid()), schema='familycare')
    op.create_foreign_key('fk_care_profiles_parent_profile_id_care_profiles', 'care_profiles', 'care_profiles',
                         ['parent_profile_id'], ['id'], source_schema='familycare', referent_schema='familycare', ondelete='SET NULL')
    op.create_check_constraint(op.f('ck_care_profiles_profile_type'), 'care_profiles', "profile_type IN ('self','member')", schema='familycare')
    op.create_index('uq_care_profiles_self_owner', 'care_profiles', ['owner_id'], unique=True,
                    postgresql_where=sa.text("profile_type = 'self'"), schema='familycare')
    profile_indexes = {item['name'] for item in sa.inspect(op.get_bind()).get_indexes('care_profiles', schema='familycare')}
    if 'ix_care_profiles_owner_id' not in profile_indexes:
        op.create_index('ix_care_profiles_owner_id', 'care_profiles', ['owner_id'], schema='familycare')
    if 'ix_care_profiles_referred_doctor_id' not in profile_indexes:
        op.create_index('ix_care_profiles_referred_doctor_id', 'care_profiles', ['referred_doctor_id'], schema='familycare')
    if 'care_reports' not in tables:
        op.create_table('care_reports', sa.Column('id', sa.Uuid(), primary_key=True),
            sa.Column('profile_id', sa.Uuid(), sa.ForeignKey('familycare.care_profiles.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(255), nullable=False), sa.Column('content_type', sa.String(80), nullable=False),
            sa.Column('content', sa.LargeBinary()), sa.Column('created_at', sa.DateTime(), nullable=False), schema='familycare')
    else:
        op.alter_column('care_reports', 'content', existing_type=sa.LargeBinary(), nullable=True, schema='familycare')
    columns = [sa.Column('storage_provider', sa.String(16), nullable=False, server_default='database'),
        sa.Column('cloudinary_public_id', sa.String(512)), sa.Column('cloudinary_asset_id', sa.String(100)),
        sa.Column('secure_url', sa.Text()), sa.Column('folder', sa.String(512)),
        sa.Column('resource_type', sa.String(16)), sa.Column('delivery_type', sa.String(20)),
        sa.Column('file_format', sa.String(20)), sa.Column('size_bytes', sa.Integer())]
    for column in columns:
        op.add_column('care_reports', column, schema='familycare')
    op.create_unique_constraint('uq_care_reports_cloudinary_public_id', 'care_reports', ['cloudinary_public_id'], schema='familycare')
    report_indexes = {item['name'] for item in sa.inspect(op.get_bind()).get_indexes('care_reports', schema='familycare')}
    if 'ix_care_reports_profile_id' not in report_indexes:
        op.create_index('ix_care_reports_profile_id', 'care_reports', ['profile_id'], schema='familycare')


def downgrade():
    raise RuntimeError('Medical report/profile downgrade is destructive; restore a reviewed backup.')
