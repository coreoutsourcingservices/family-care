"""Add ten labelled Admin demo articles, without replacing existing content."""
import argparse
from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select
from app import create_app
from core.database import db
from core.models import HealthArticle, User, now
from services.repository import audit

DIET = 'https://www.who.int/news-room/fact-sheets/detail/healthy-diet'
PREGNANCY = 'https://www.who.int/tools/elena/interventions/nutrition-counselling-pregnancy'
SAMPLES = [
    ('cycle', 'Period diary: getting started', 'Each cycle', None,
     'Use the Period & cycle diary to record the start date, end date and any notes you want to discuss. Add entries from your own observations. This sample article does not calculate ovulation or diagnose a condition.'),
    ('cycle', 'Prepare your cycle questions', 'Before a consultation', None,
     'Before your appointment, collect the dates and symptoms you would like to discuss. Note which changes concern you and any medicines you already take. Share only the tabs you want your connected doctor to access.'),
    ('pcos', 'Organise your hormonal health notes', 'Before a consultation', None,
     'Use PCOS & hormonal to keep your questions, existing clinician reports and symptom notes together. A diary entry is not a PCOS diagnosis. Ask your clinician to explain any diagnosis, test result or treatment already recommended to you.'),
    ('pregnancy', 'Your pregnancy care notebook', 'Throughout pregnancy', None,
     'Keep appointment questions and existing scan or test reports in one place. Confirm the pregnancy stage with your maternity clinician before saving it. The saved stage helps FamilyCare display month-specific articles from Admin and your connected doctor.'),
    ('pregnancy', 'Month 3: discuss food and nutrition', 'Month 3', 3,
     'WHO recommends healthy-eating counselling during pregnancy. Use your next visit to discuss foods you can tolerate, dietary preferences and any existing restrictions with your maternity clinician. This sample does not prescribe a meal plan or supplements.\n\nSource: '+PREGNANCY),
    ('fertility', 'Build a reproductive health question list', 'Before a consultation', None,
     'Write down your reproductive health questions and bring relevant existing reports to your consultation. Keep your goals and concerns in your own words. This demo article does not predict fertility, pregnancy chances or treatment outcomes.'),
    ('symptoms', 'Make your wellbeing notes useful', 'Daily check-in', None,
     'When you choose to record a symptom, include when you noticed it and what you want to ask your doctor. You can keep personal notes in your diary and decide which tabs to share. This sample is for organising notes and is not a diagnosis or an emergency service.'),
    ('nutrition', 'Variety in everyday food choices', 'Daily routine', None,
     'WHO describes variety as part of a healthy diet, including vegetables, fruit, pulses, whole grains and suitable protein foods. Use your nutrition diary to record your usual choices and questions. Individual needs vary; discuss personal dietary restrictions with your clinician.\n\nSource: '+DIET),
    ('nutrition', 'Prepare for a lifestyle discussion', 'Before a consultation', None,
     'Use Nutrition & lifestyle to note your usual meals, activities and routines. List one or two questions you want to discuss with your care team. This sample does not set calorie targets, prescribe exercise or change an existing treatment plan.'),
    ('screening', 'Keep preventive care records together', 'Before a consultation', None,
     'Bring existing screening reports and any follow-up instructions to your next consultation. Ask your clinician which checks and follow-up dates apply to your age and history. Save confirmed dates in your planner rather than treating this demo as a screening schedule.'),
]


def seed(admin_id=None):
    query = select(User).where(User.role == 'ADMIN', User.account_status == 'ACTIVE', User.approval_status == 'APPROVED', User.email_verified.is_(True))
    if admin_id:
        query = query.where(User.id == admin_id)
    admin = db().scalar(query.order_by(User.created_at, User.id))
    if not admin:
        raise RuntimeError('An active approved Admin account is required')
    added = skipped = 0
    for index, (category, title, time_label, month, body) in enumerate(SAMPLES):
        identifier = str(uuid5(NAMESPACE_URL, f'familycare:women-admin-demo-articles:v1:{index}'))
        if db().get(HealthArticle, identifier):
            skipped += 1
            continue
        db().add(HealthArticle(id=identifier, author_id=admin.id, title='DEMO - '+title,
            audience='women', category=category, stage_month=month, time_label=time_label,
            summary='Demo article for the Women Health workspace.',
            content='DEMO ARTICLE\n\n'+body, tags=['demo'], status='PUBLISHED', published_at=now()))
        audit('health_article_demo_created', admin.id, admin.id)
        added += 1
    db().commit()
    return dict(added=added, skipped=skipped, total_demo=len(SAMPLES), author_role=admin.role)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admin-id')
    args = parser.parse_args()
    with create_app().app_context():
        print(seed(args.admin_id))
