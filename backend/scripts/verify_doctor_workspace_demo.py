"""Read the seeded doctor samples through the same scoped services as the UI."""
from datetime import timedelta
from flask import g
from sqlalchemy import select
from app import create_app
from core.database import db
from core.models import User,CareProfile,DoctorConsultation,CapacityAppointment
from scripts.seed_doctor_workspace_demo import identifier
from services import care,prescriptions,adult_workspace,women_workspace,care_uploads
from doctor.clinical_records import records
from services.capacity_appointments import today

def verify():
 app=create_app()
 with app.test_request_context():
  doctor=db().scalar(select(User).where(User.email=='eeshapillai3@gmail.com',User.role=='DOCTOR'))
  g.user=doctor
  result=[]
  for key in ['ama','pk','saif','riya']:
   p=db().get(CareProfile,identifier(doctor.id,key+'-profile'))
   assert p and p.referred_doctor_id==doctor.id and '(DEMO)' in p.name
   if p.module=='child':
    history=records(p.id).get_json()['items'];reports=care.list_reports(doctor,p.id,1,100).get_json()['items'];download=lambda report:care_uploads.download_report(doctor,p.id,report)
   elif p.module=='adult':
    history=adult_workspace.workspace(p.id).get_json()['records'];reports=adult_workspace.report_list(p.id).get_json()['items'];download=lambda report:adult_workspace.download(p.id,report)
   else:
    history=women_workspace.workspace(p.id).get_json()['records'];reports=women_workspace.reports(p.id).get_json()['items'];download=lambda report:women_workspace.download(p.id,report)
   assert len(history)>=4 and len(reports)==2, (p.name,len(history),len(reports))
   for r in reports:
    response=download(r['id']);response.direct_passthrough=False;assert response.get_data().startswith(b'%PDF-1.4')
   rx=prescriptions.listing(p.id).get_json()['items'];assert len(rx)==1 and rx[0]['status']=='DRAFT'
   visits=db().scalars(select(DoctorConsultation).where(DoctorConsultation.profile_id==p.id,DoctorConsultation.doctor_id==doctor.id)).all();assert len(visits)==2
   bookings=db().scalars(select(CapacityAppointment).where(CapacityAppointment.profile_id==p.id,CapacityAppointment.doctor_id==doctor.id)).all();assert len(bookings)==1 and not bookings[0].email_id
   result.append(dict(name=p.name,module=p.module,records=len(history),reports=len(reports),drafts=len(rx),consultations=len(visits),booking_date=bookings[0].appointment_date.isoformat()))
  print({'verified_doctor':doctor.full_name,'patients':result,'pdf_downloads_checked':8},flush=True)
if __name__=='__main__':verify()
