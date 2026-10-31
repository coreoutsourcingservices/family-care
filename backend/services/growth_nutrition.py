"""Default-active, DOB-selected educational content with per-child doctor control."""
import json
from functools import lru_cache
from pathlib import Path
from flask import Blueprint,g,jsonify
from pydantic import StrictBool
from core.schemas import Schema,parse
from core.database import db
from core.models import ChildGrowthNutritionSetting,now
from core.routing import route
from services.repository import audit
from patient.child_routes import child,child_age

bp=Blueprint('growth_nutrition',__name__,url_prefix='/api/v1')

class GuideVisibility(Schema):
    active: StrictBool

@lru_cache(maxsize=1)
def content():
    return json.loads((Path(__file__).resolve().parents[1]/'content'/'child_growth_nutrition.json').read_text(encoding='utf-8'))

def state(profile):
    row=db().get(ChildGrowthNutritionSetting,profile.id)
    age=child_age(profile);active=row.active if row else True
    return dict(child=dict(id=profile.id,full_name=profile.name,date_of_birth=profile.dob.isoformat(),age=age),
        active=active,default_active=True,status='INACTIVE' if not active else 'OUT_OF_SCOPE' if not age['in_child_module_scope'] else 'AVAILABLE',
        updated_at=row.updated_at.isoformat()+'Z' if row else None,
        updated_by=row.updated_by if row else None,version=content()['version'])

def read(profile_id):
    profile=child(profile_id);result=state(profile);data=content()
    result['age_band']=None;result['guide']=None
    if result['status']=='AVAILABLE':
        months=result['child']['age']['total_completed_months']
        band=next(b for b in data['age_bands'] if b['min_months']<=months<b['max_months_exclusive'])
        result['age_band']={k:band[k] for k in ('id','label','min_months','max_months_exclusive')}
        result['guide']=dict(title=data['title'],nutrition=band,growth_monitoring=data['growth_monitoring'],
            food_safety=data['food_safety'],sources=data['sources'],notice=data['notice'],provenance=data['provenance'])
    return jsonify(**result)

def set_visibility(profile_id):
    profile=child(profile_id,lock=True);value=parse(GuideVisibility)
    row=db().get(ChildGrowthNutritionSetting,profile.id)
    if not row:
        row=ChildGrowthNutritionSetting(profile_id=profile.id,active=value.active,updated_by=g.user.id);db().add(row)
    else:row.active=value.active;row.updated_by=g.user.id;row.updated_at=now()
    audit('growth_nutrition_activated' if value.active else 'growth_nutrition_deactivated',profile.owner_id,g.user.id)
    db().flush()
    from services.notifications import enqueue
    enqueue(profile.owner_id,'growth_nutrition_updated','Growth & Nutrition guide updated',
        'Your connected doctor '+('activated' if value.active else 'deactivated')+' the age-based guide for this child.',
        {'profile_id':profile.id,'area':'growth'})
    db().commit()
    return jsonify(**state(profile))

route(bp,'/children/<uuid:profile_id>/growth-nutrition-guide',read,roles=('PATIENT',))
def doctor_read(profile_id):return read(profile_id)
route(bp,'/doctors/care-profiles/<uuid:profile_id>/growth-nutrition-guide',doctor_read,roles=('DOCTOR',))
route(bp,'/doctors/care-profiles/<uuid:profile_id>/growth-nutrition-guide/visibility',set_visibility,'PATCH',roles=('DOCTOR',),schema=GuideVisibility)
