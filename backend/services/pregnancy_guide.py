"""WHO-sourced education, not an individual treatment plan or WHO endorsement."""
from datetime import date
from flask import Blueprint,g,jsonify
from pydantic import Field,model_validator
from sqlalchemy import select
from core.database import db
from core.models import PregnancyCare,CareProfile,User,now
from core.errors import APIError
from core.schemas import Schema,parse
from core.routing import route
from services.women_workspace import get_profile,primary_id
from services.repository import audit

bp=Blueprint('pregnancy_guide',__name__,url_prefix='/api/v1/women')
MONTHS=[(1,4),(5,8),(9,13),(14,17),(18,22),(23,27),(28,31),(32,35),(36,40)]
SOURCES=[
 {'id':'anc','title':'WHO antenatal care recommendations','url':'https://www.who.int/publications/i/item/9789241549912'},
 {'id':'schedule','title':'WHO antenatal contact schedule','url':'https://www.who.int/news/item/07-11-2016-new-guidelines-on-antenatal-care-for-a-positive-pregnancy-experience'},
 {'id':'activity','title':'WHO physical activity guidelines','url':'https://www.who.int/publications/i/item/9789240015128'},
 {'id':'warnings','title':'WHO pregnancy warning signs','url':'https://www.who.int/campaigns/world-health-day/2025/key-messages'},
 {'id':'food_safety','title':'WHO five keys to safer food','url':'https://www.who.int/activities/promoting-safe-food-handling/five-key-to-safer-food'}]

class Stage(Schema):
    month:int|None=Field(default=None,ge=1,le=9,strict=True)
    week:int|None=Field(default=None,ge=1,le=42,strict=True)
    as_of_date:date=Field(default_factory=date.today)
    active:bool=True
    version:int=Field(default=0,ge=0)
    @model_validator(mode='after')
    def validate_stage(self):
        if (self.month is None)==(self.week is None):raise ValueError('Provide either month (1-9) or week (1-42)')
        if self.as_of_date>date.today():raise ValueError('As-of date cannot be in the future')
        return self

def current_week(row):return row.baseline_week+(date.today()-row.as_of_date).days//7

def guide(week,approximate=False):
    month=next((i+1 for i,(start,end) in enumerate(MONTHS) if start<=week<=end),9 if week>40 else None)
    trimester=1 if week<=13 else 2 if week<=27 else 3
    focus={1:'Arrange early antenatal care and discuss nutrition, supplements and any existing conditions.',2:'Keep antenatal contacts and discuss your blood tests, scan results and any symptoms.',3:'Review your birth plan, transport and support person with your maternity team.'}[trimester]
    if week>40:focus='Contact your maternity team to agree follow-up now, especially at or beyond 41 weeks.'
    contacts=[12,20,26,30,34,36,38,40]
    return dict(title='Pregnancy Care Guide',attribution='Based on WHO guidance; adapted by FamilyCare+',sources=SOURCES,
      week=week,month=month,trimester=trimester,approximate=approximate,needs_stage_review=week>42,
      stage_note='Month-to-week ranges are approximate; confirm gestational age with your clinician.' if approximate else 'Week is based on the value you entered, not a medical assessment.',
      focus=focus if week<=42 else 'Your saved stage is over 42 weeks. Contact your maternity team promptly and update or turn off this guide.',
      food=[dict(text='Choose varied foods: vegetables, fruit, whole grains, beans, nuts and suitable protein foods.',source='anc'),dict(text='Use safe water, wash produce, separate raw and cooked food, cook thoroughly and refrigerate perishables promptly. Choose pasteurized milk.',source='food_safety'),dict(text='Discuss iron and folic acid with your antenatal clinician; follow the prescribed dose rather than starting or changing supplements here.',source='anc')],
      daily_care=[dict(text='If your maternity clinician has not advised against activity, build up regular moderate activity; WHO recommends at least 150 minutes per week for pregnant women without contraindications.',source='activity'),dict(text='Discuss tobacco, alcohol or other substance use and any medicines with your antenatal clinician.',source='anc'),dict(text='Discuss nausea, back pain, constipation, emotional wellbeing and any new symptoms at your visits.',source='anc')],
      checkups=dict(source='schedule',contact_weeks=contacts,first_contact='First contact within the first 12 weeks; arrange care now if you have not started.',next_contact_week=next((w for w in contacts if w>=week),None),note='WHO recommends at least 8 antenatal contacts. Your clinician may arrange additional or different visits. Discuss an ultrasound before 24 weeks.'),
      urgent=dict(source='warnings',action='Seek urgent medical care immediately; do not wait for an app notification or routine visit.',signs=['Vaginal bleeding or severe abdominal pain','Persistent severe headache, blurred vision or sudden swelling','Changes or reduction in your baby’s usual movements','An injury to your abdomen']),
      disclaimer='General education only. Diet, activity, tests and treatment must be adapted by your maternity clinician, especially for a high-risk pregnancy.')

def preview():
    value=parse(Stage);week=value.week or MONTHS[value.month-1][0]
    return jsonify(guide=guide(week,value.month is not None))

def settings_data(row):return dict(week=row.baseline_week,month=row.input_month,as_of_date=row.as_of_date.isoformat(),active=row.active,version=row.version)
def read_care(profile_id):
    profile,_=get_profile(profile_id,'pregnancy')
    row=db().get(PregnancyCare,profile.id)
    return jsonify(settings=settings_data(row) if row else None,guide=guide(current_week(row),row.input_month is not None) if row and row.active else None)

def save_care(profile_id):
    profile,_=get_profile(profile_id,'pregnancy',edit=True,manage=True)
    value=parse(Stage)
    if value.as_of_date<profile.dob:raise APIError(422,'invalid_date','As-of date cannot be before date of birth')
    row=db().get(PregnancyCare,profile.id)
    if row and row.version!=value.version or not row and value.version!=0:raise APIError(409,'stage_changed','Refresh the pregnancy stage before saving')
    if not row:row=PregnancyCare(profile_id=profile.id,version=0);db().add(row)
    row.baseline_week=value.week or MONTHS[value.month-1][0];row.input_month=value.month
    row.as_of_date=value.as_of_date;row.active=value.active;row.updated_by=g.user.id;row.version+=1
    if row.active:notify(row,profile)
    audit('pregnancy_care_updated',profile.owner_id,g.user.id);db().commit()
    return jsonify(settings=settings_data(row),guide=guide(current_week(row),row.input_month is not None) if row.active else None)

def notify(row,profile):
    week=current_week(row)
    if not 1<=week<=42:return
    from services.notifications import enqueue
    enqueue(primary_id(profile),'pregnancy_guide','Pregnancy Care Guide','Your weekly care guide is ready. Based on WHO guidance; open it to review the sources.',{'profile_id':profile.id,'module':'women','area':'pregnancy_guide'},event_key='pregnancy-guide:'+profile.id+':'+row.as_of_date.isoformat()+':'+str(row.baseline_week)+':'+str(week))

def scan_guides():
    for row in db().scalars(select(PregnancyCare).where(PregnancyCare.active.is_(True)).with_for_update()).all():
        profile=db().get(CareProfile,row.profile_id)
        if not profile or profile.deleted_at:continue
        user=db().get(User,primary_id(profile))
        if user and user.email_verified and user.approval_status=='APPROVED' and user.account_status=='ACTIVE':notify(row,profile)
    db().commit()

route(bp,'/pregnancy-guide',preview,'POST',roles=('PATIENT','DOCTOR'),schema=Stage)
route(bp,'/profiles/<uuid:profile_id>/pregnancy-care',read_care,roles=('PATIENT','DOCTOR'))
route(bp,'/profiles/<uuid:profile_id>/pregnancy-care',save_care,'PUT',roles=('PATIENT',),schema=Stage)
