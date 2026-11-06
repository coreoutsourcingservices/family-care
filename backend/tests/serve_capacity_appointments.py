"""Temporary SQLite-only appointment browser QA; never starts mail delivery."""
from serve_women_workspace import app
from core.database import db
from core.models import CareProfile

with app.app_context():
    db().get(CareProfile, '66666666-6666-4666-8666-666666666666').referred_doctor_id = '33333333-3333-4333-8333-333333333333'
    db().commit()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5003, threaded=False, use_reloader=False)
