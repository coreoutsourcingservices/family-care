from copy import deepcopy
from services.growth_nutrition import content

def enrich(paths):
    data=content();band=deepcopy(data['age_bands'][8])
    state=dict(child=dict(id='<child UUID>',full_name='Example Child',date_of_birth='2026-02-28',
        age=dict(completed_years=0,remaining_months=8,remaining_days=3,total_completed_months=8,total_days=245,
            display='0 years 8 months 3 days',primary_category='INFANT',secondary_categories=[],in_child_module_scope=True)),
        active=True,default_active=True,status='AVAILABLE',updated_at=None,updated_by=None,version=data['version'])
    for path,methods in paths.items():
        if 'growth-nutrition-guide' not in path:continue
        for method,op in methods.items():
            example=deepcopy(state)
            if method=='patch':
                op['requestBody']['content']['application/json']['example']={'active':False}
                example.update(active=False,status='INACTIVE',updated_at='<UTC timestamp>',updated_by='<connected doctor UUID>')
                op['description']+='. Changes only this child. Saved measurements and meal notes remain available. active must be a JSON boolean.'
            else:
                example.update(age_band={k:band[k] for k in ('id','label','min_months','max_months_exclusive')},
                    guide=dict(title=data['title'],nutrition=band,growth_monitoring=data['growth_monitoring'],food_safety=data['food_safety'],
                        sources=data['sources'],notice=data['notice'],provenance=data['provenance']))
                op['description']+='. Default active for all children. Uses DOB and India calendar; no rows need to be provisioned. Inactive or age 13+ returns guide: null.'
            op['responses']={k:v for k,v in op['responses'].items() if not k.startswith('2')}
            op['responses']['200']={'description':'Success','content':{'application/json':{'example':example}}}
