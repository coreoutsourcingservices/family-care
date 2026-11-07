"""Consultation modes, fees and booking context."""
from alembic import op
import sqlalchemy as sa
revision = '0034_consultation_booking'
down_revision = '0033_capacity_appointments'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('doctor_profiles', sa.Column('consultation_options', sa.JSON()), schema='familycare')
    op.add_column('capacity_appointments', sa.Column('booking_details', sa.JSON()), schema='familycare')

def downgrade():
    op.drop_column('capacity_appointments', 'booking_details', schema='familycare')
    op.drop_column('doctor_profiles', 'consultation_options', schema='familycare')
