"""Synthetic historical examples, never real clinical conclusions."""
from datetime import timedelta


def entries(anchor):
    rows = []
    def add(section, key, days, title, **fields):
        rows.append((key, section, dict(date=(anchor + timedelta(days=days)).isoformat(), title='DEMO - '+title,
            notes='DEMO / SAMPLE ONLY. Fictional history for previewing this workspace. '+fields.pop('notes', ''), **fields)))
    for i in range(6):
        ago = -150 + i*28
        add('health', f'health-visit-{i}', ago, f'Health review {i+1}', category='Visit', notes='Example visit summary and questions for the next review.')
    for i, category in enumerate(['General health','Condition','Medication','Allergy']):
        add('health', f'health-type-{i}', -210+i*20, category+' history example', category=category, notes='Example entry only; no actual condition, medication or allergy is asserted.')
    for i in range(10):
        start = -312+i*28
        add('cycle', f'cycle-{i}', start, f'Historical cycle {i+1}', end=(anchor+timedelta(days=start+4)).isoformat(), flow=['Light','Medium','Heavy'][i%3], symptoms=['Mild cramps','Low energy','No symptoms noted'][i%3])
    for i, category in enumerate(['Symptoms','Lab test','Treatment','Clinician diagnosis']):
        add('pcos', f'pcos-{i}', -120+i*27, category+' example', category=category, severity=['Mild','Moderate','Severe','Mild'][i], diagnosis_source='Self-reported symptoms', notes='Fictional PCOS/hormonal topic example, not a confirmed diagnosis or treatment plan.')
    for i, (category, week, ago) in enumerate([('Antenatal visit','10',-420),('Scan','20',-350),('Antenatal visit','30',-280),('Symptom','37',-231),('Postnatal care','40',-175)]):
        add('pregnancy', f'pregnancy-{i}', ago, category+' historical example', category=category, week=week, due=(anchor-timedelta(days=210)).isoformat(), due_source='Not confirmed', pregnancy_status='Postpartum' if i==4 else 'Ended', ended_on=(anchor-timedelta(days=215)).isoformat(), notes='Fictional completed pregnancy history; this does not indicate a current pregnancy.')
    for i, category in enumerate(['Question for doctor','Consultation','Test','Care plan']):
        add('fertility', f'fertility-{i}', -110+i*25, category+' example', category=category, notes='Fictional reproductive-health questions and discussion notes. No fertility diagnosis.')
    for i, symptom in enumerate(['Cramps','Headache','Fatigue','Bloating','Sleep changes','Mood changes','Wellbeing follow-up','Energy journal','Symptom review']):
        add('symptoms', f'symptoms-{i}', -90+i*10, symptom+' example', severity=['Mild','Moderate','Severe'][i%3], notes='Example symptom journal only; not an assessment of the account holder.')
    for i in range(6):
        for j, category in enumerate(['Meals','Hydration','Movement','Sleep']):
            add('nutrition', f'nutrition-{i}-{j}', -120+i*20+j, category+' journal '+str(i+1), category=category, notes={'Meals':'Example meal: rice, dal, vegetables and fruit.','Hydration':'Example hydration journal: water with meals.','Movement':'Example activity: a short evening walk.','Sleep':'Example journal: bedtime and morning energy noted.'}[category])
    for i, category in enumerate(['Cervical screening','Breast screening','HPV vaccination','Other screening']):
        for j, status in enumerate(['Completed','Planned']):
            add('screening', f'screening-{i}-{j}', -160+i*25+j*12, category+' example '+status.lower(), category=category, status=status, next=(anchor+timedelta(days=30+i*7)).isoformat(), notes='Fictional screening record only; no real test result or vaccination is asserted.')
    for i in range(6):
        add('consultation', f'consultation-{i}', -150+i*25, 'Saved visit notes '+str(i+1), doctor='Demo clinician (fictional)', status='Completed', notes='Fictional previous consultation note; no appointment request or message was sent to a real doctor.')
    for i in range(7):
        add('checkin', f'checkin-{i}', -6+i, 'Wellbeing check-in '+str(i+1), mood=['Calm','Good','Tired','Good','Calm','Good','Good'][i], notes='Fictional daily check-in.')
    for i, days in enumerate([-60,-30,-7,3,7,14]):
        add('reminder', f'reminder-{i}', days, 'Diary reminder '+str(i+1), status='Completed' if days<0 else 'Planned')
    return rows
