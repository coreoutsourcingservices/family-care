"""User-requested reference schedules. Imports are drafts, never medical attestations."""
from flask import g, jsonify
from sqlalchemy import select
from core.database import db
from core.models import Vaccine, VaccineSchedule
from core.vaccination_schemas import VaccineInput, ScheduleInput
from core.http import pagination
from core.errors import APIError
from services import vaccination as v
from services.approvals import paginate

VERSION = 'familycare-0-12-2026-v1'
SOURCES = {
 'UIP': 'https://risemohfw.in/rise-guidelines',
 'IAP': 'https://www.indianpediatrics.net/may2026/311.pdf',
}
CATALOG = {
 'BCG':('BCG','Tuberculosis','ID'), 'OPV':('OPV','Polio','Oral'),
 'HEPB':('Hepatitis B','Hepatitis B','IM'), 'PENTA':('Pentavalent','Diphtheria, pertussis, tetanus, hepatitis B and Hib','IM'),
 'RVV':('Rotavirus','Rotavirus diarrhea','Oral'), 'FIPV':('fIPV','Polio','ID'),
 'PCV':('PCV','Pneumococcal infection','IM'), 'MR':('MR','Measles and rubella','SC'),
 'JE':('JE','Japanese encephalitis','Other'), 'DPT':('DPT','Diphtheria, pertussis and tetanus','IM'),
 'TD':('Td','Tetanus and diphtheria','IM'), 'FLU':('Influenza','Seasonal influenza','IM'),
 'TCV':('Typhoid conjugate vaccine','Typhoid','IM'), 'MMR':('MMR','Measles, mumps and rubella','SC'),
 'HEPA':('Hepatitis A','Hepatitis A','Other'), 'VAR':('Varicella','Chickenpox','SC'),
 'IPV':('IPV','Polio','IM'), 'HIB':('Hib','Haemophilus influenzae type B','IM'),
 'HPV':('HPV','Human papillomavirus and related cancers','IM'), 'TDAP':('Tdap','Tetanus, diphtheria and pertussis','IM'),
}
# code, dose code, label, unit, start, end, prerequisite, minimum interval days
UIP = [('BCG','BCG','Birth','days',0,0,'',None),('OPV','OPV0','Birth dose','days',0,14,'',None),('HEPB','HEPB0','Birth dose','days',0,0,'',None)]
for number,week in enumerate((6,10,14),1):
 for code in ('OPV','PENTA','RVV'):
  UIP.append((code,f'{code}{number}',f'Dose {number}','weeks',week,week,f'{code}{number-1}' if number>1 else '',28 if number>1 else None))
UIP += [('FIPV','FIPV1','Dose 1','weeks',6,6,'',None),('PCV','PCV1','Dose 1','weeks',6,6,'',None),
 ('FIPV','FIPV2','Dose 2','weeks',14,14,'FIPV1',56),('PCV','PCV2','Dose 2','weeks',14,14,'PCV1',56),
 ('MR','MR1','Dose 1','months',9,12,'',None),('FIPV','FIPV3','Dose 3','months',9,12,'FIPV2',28),
 ('PCV','PCVB','Booster','months',9,12,'PCV2',56),('JE','JE1','Dose 1 - selected districts','months',9,12,'',None),
 ('MR','MR2','Dose 2','months',16,24,'MR1',28),('DPT','DPTB1','Booster 1','months',16,24,'',None),
 ('OPV','OPVB','Booster','months',16,24,'OPV3',28),('JE','JE2','Dose 2 - selected districts','months',16,24,'JE1',90),
 ('DPT','DPTB2','Booster 2','years',5,6,'DPTB1',180),('TD','TD10','Dose at 10 years','years',10,10,'',None)]
IAP = [('FLU','FLU1','Dose 1','months',6,6,'',None),('FLU','FLU2','Dose 2','months',7,7,'FLU1',28),
 ('TCV','TCV1','Dose 1','months',6,9,'',None),('MMR','MMR1','Dose 1','months',9,9,'',None),
 ('HEPA','HEPA1','Dose 1','months',12,12,'',None),('MMR','MMR2','Dose 2','months',15,15,'MMR1',28),
 ('VAR','VAR1','Dose 1','months',15,15,'',None),('PCV','PCVB','Booster','months',15,15,'',None),
 ('DPT','DPTB1','Booster','months',16,18,'',None),('IPV','IPVB1','Booster','months',16,18,'',None),
 ('HIB','HIBB','Booster','months',16,18,'',None),('HEPA','HEPA2','Dose 2 when applicable','months',18,19,'HEPA1',180),
 ('VAR','VAR2','Dose 2','months',18,19,'VAR1',90),('DPT','DPTB2','Booster','years',4,6,'DPTB1',180),
 ('IPV','IPVB2','Booster','years',4,6,'IPVB1',180),('MMR','MMRB','Booster','years',4,6,'MMR2',28),
 ('HPV','HPV1','Doctor-selected regimen','years',9,12,'',None),('TDAP','TDAP10','Dose at 10 years','years',10,10,'',None)]

def import_starter(scheme, actor_id):
 created = skipped = 0
 for code,dose,label,unit,start,end,previous,interval in (UIP if scheme=='UIP' else IAP):
  vaccine=db().scalar(select(Vaccine).where(Vaccine.code=='FC_'+code))
  if not vaccine:
   name,disease,route=CATALOG[code]
   data=VaccineInput(code='FC_'+code,name_en=name,category='Government' if code in {r[0] for r in UIP} else 'Optional',protects_against=disease).model_dump(mode='json')
   vaccine=Vaccine(code=data['code'],data=data,active=True);db().add(vaccine);db().flush()
  if db().scalar(select(VaccineSchedule.id).where(VaccineSchedule.vaccine_id==vaccine.id,VaccineSchedule.schedule_type==scheme,VaccineSchedule.dose_code==dose,VaccineSchedule.version==VERSION)):
   skipped+=1;continue
  notes='Routine reference window; review source, prior doses and product before publication. Do not generate catch-up dates automatically.'
  if scheme=='IAP':notes+=' Reconcile with UIP records to avoid duplicate doses.'
  if code=='JE':notes+=' Only in applicable endemic districts; doctor must confirm district eligibility and vaccine product.'
  if code=='HPV':notes+=' Number of doses depends on age, product, immune status and current clinical guidance.'
  if code=='HEPA':notes+=' Confirm formulation: a second dose is only for an applicable two-dose regimen.'
  if code=='HEPB':notes+=' Birth dose within 24 hours.'
  if code=='FLU':notes+=' Second initial dose at least four weeks later. Review annual influenza doses through age five separately.'
  data=ScheduleInput(vaccine_id=vaccine.id,schedule_type=scheme,dose_code=dose,dose_name=label,version=VERSION,
   age_label=('At birth' if start==0 else f'{start}'+(f'–{end}' if end!=start else '')+f' {unit}'),age_unit=unit,age_start=start,age_end=end,
   previous_dose_code=previous,minimum_interval_days=interval,route=CATALOG[code][2],instructions=notes,
   source_url=SOURCES[scheme],source_reference=('MoHFW RISE national schedule and fIPV3 guidance; verify exact windows' if scheme=='UIP' else 'IAP-ACVIP 2025 recommendations, Indian Pediatrics 2026; additional schedule subset'),
   effective_from=v.today(),eligibility={'requires_clinical_review':scheme=='IAP' or code=='JE','programme':scheme},
   reminders={'before_days':[7,1],'overdue_days':[1,7],'language':'hi','email':False}).model_dump(mode='json')
  data['vaccine']=v.vaccine_data(vaccine)
  row=VaccineSchedule(vaccine_id=vaccine.id,schedule_type=scheme,dose_code=dose,version=VERSION,created_by=actor_id,data=data)
  db().add(row);db().flush();v.log('starter_imported',schedule=row);created+=1
 db().commit()
 return dict(created=created,skipped=skipped,schedule_type=scheme,message='Drafts saved. Independent medical review and admin publication are required.')

def import_uip():return jsonify(import_starter('UIP',g.user.id))
def import_iap():
 v.qualified_reviewer(g.user.id)
 return jsonify(import_starter('IAP',g.user.id))
def doctor_schedules():
 v.qualified_reviewer(g.user.id)
 page,size=pagination();rows,total=paginate(select(VaccineSchedule).where(VaccineSchedule.schedule_type=='IAP').order_by(VaccineSchedule.created_at,VaccineSchedule.id),page,size)
 return jsonify(items=[v.schedule_data(row,True) for row in rows],total=total,page=page,per_page=size)
def own_draft(schedule_id):
 v.qualified_reviewer(g.user.id);row=v.schedule_row(schedule_id,True)
 if row.schedule_type!='IAP' or row.created_by!=g.user.id:raise APIError(403,'not_your_draft','Only your IAP drafts can be changed')
 v.require_draft(row)
 return row
def doctor_edit(schedule_id):
 from core.schemas import parse
 row=own_draft(schedule_id);data=parse(ScheduleInput).model_dump(mode='json')
 if data['schedule_type']!='IAP' or data['vaccine_id']!=row.vaccine_id:raise APIError(422,'invalid_scheme','Keep this draft within its IAP vaccine')
 return v.edit_schedule(schedule_id)
def doctor_submit(schedule_id):
 own_draft(schedule_id)
 return v.submit_review(schedule_id)
