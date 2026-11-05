"""Valid synthetic Adult Health examples; no diagnosis or treatment advice."""
from datetime import timedelta


def entries(anchor):
    rows=[]
    def add(kind,key,offset,title,**fields):
        rows.append((key,dict(kind=kind,date=(anchor+timedelta(days=offset)).isoformat(),title='DEMO - '+title,
            notes='DEMO / SAMPLE ONLY. Fictional entry for workspace preview. '+fields.pop('notes',''),**fields)))
    for i in range(24):
        add('bp',f'bp-{i}',-168+i*7,'Blood pressure reading '+str(i+1),systolic=116+i%8,diastolic=74+i%5,pulse=68+i%9,arm='Left' if i%2 else 'Right',position='Seated',measurement_time='08:30')
    for i in range(18):
        add('glucose',f'glucose-{i}',-170+i*10,'Blood sugar reading '+str(i+1),glucose=88+i%13 if i%2==0 else 112+i%17,units='mg/dL',reading_context='Fasting' if i%2==0 else 'Post-meal',meal_minutes=0 if i%2==0 else 120,context='Fasting' if i%2==0 else 'After meal')
    for i in range(6):
        add('lipids',f'lipids-{i}',-180+i*30,'Lipid panel '+str(i+1),total=174+i*2,ldl=96+i,hdl=52+i%4,triglycerides=118+i*3,context='Synthetic laboratory panel')
    for i in range(4):
        add('medicine',f'medicine-{i}',-120+i*28,'Medicine journal example '+str(i+1),context='DEMO PLACEHOLDER, not a real medicine',strength='Not applicable - sample',dose='Not applicable - sample',frequency='Example field only',adherence=['Not recorded','Taken','Missed','Not recorded'][i],start_date=(anchor-timedelta(days=120-i*28)).isoformat(),end_date=(anchor-timedelta(days=113-i*28)).isoformat(),status='Completed',notes='No medicine is prescribed by this fictional example.')
    for i in range(6):
        for j,context in enumerate(['Walking','Sleep','Meals','Hydration']):
            add('lifestyle',f'lifestyle-{i}-{j}',-100+i*16+j,context+' journal '+str(i+1),context=context,minutes=20+i*2 if j==0 else 0,sleep_hours=7.0+i%3*.25 if j==1 else None,notes={'Walking':'Example evening walk.','Sleep':'Example bedtime and rest journal.','Meals':'Example meal: rice, dal, vegetables and fruit.','Hydration':'Example hydration diary.'}[context])
    for i,context in enumerate(['Annual health review','Dental checkup','Vision check','Vaccination discussion']):
        for j in range(2):
            add('screening',f'screening-{i}-{j}',-160+i*25+j*10,context+' example '+str(j+1),context=context,status='Completed' if j==0 else 'Planned',result_status='Completed' if j==0 else 'Scheduled',follow_up=(anchor+timedelta(days=20+i*7)).isoformat(),notes='Fictional preventive care record; no real test or vaccination is asserted.')
    for i,kind in enumerate(['Condition','Allergy','Procedure','Hospitalization','Family history']):
        add('history',f'history-{i}',-240+i*30,kind+' history example',history_type=kind,context=kind,notes='Illustrative history layout only; not an actual condition, allergy, procedure or admission.')
    for i in range(6):
        add('history',f'visit-{i}',-150+i*25,'Previous consultation notes '+str(i+1),context='DEMO consultation note',status='Completed',notes='Fictional visit discussion and questions. No real doctor appointment or message was sent.')
    for i,offset in enumerate([-60,-30,-7,3,7,14]):
        add('reminder',f'reminder-{i}',offset,'Health reminder '+str(i+1),context=['Records','Checkup','Activity'][i%3],status='Completed' if offset<0 else 'Planned')
    return rows
