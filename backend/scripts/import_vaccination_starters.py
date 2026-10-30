"""Import draft data into the configured DB. Never reviews or publishes it."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import g
from app import create_app
from core.database import db
from core.models import User
from services.vaccination import qualified_reviewer
from services.vaccination_starters import import_starter

parser=argparse.ArgumentParser()
parser.add_argument('--admin-id',required=True)
parser.add_argument('--doctor-id',required=True)
args=parser.parse_args()
app=create_app()
with app.test_request_context():
    admin=db().get(User,args.admin_id)
    if not admin or admin.role not in ('ADMIN','SUPERADMIN') or admin.account_status!='ACTIVE':
        raise SystemExit('Active administrator required')
    doctor,_=qualified_reviewer(args.doctor_id)
    # Ownership assigns where imported drafts can be edited; it is not a medical attestation.
    g.user=admin
    print(import_starter('UIP',admin.id))
    g.user=doctor
    print(import_starter('IAP',doctor.id))
