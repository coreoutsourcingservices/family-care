from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import text
from core.config import settings
from core.database import init_database, db
from core.errors import register_errors
from core.extensions import limiter
from core.security import cookie_request_guard, transport


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(settings(overrides))
    register_errors(app)
    from services.signup import PendingStore
    app.extensions['pending_signups'] = PendingStore(app.config['RATELIMIT_STORAGE_URI'])
    init_database(app)
    limiter.init_app(app)
    CORS(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}},
         supports_credentials=True, allow_headers=['Content-Type', 'Authorization', 'X-Auth-Transport',
                                                   'X-CSRF-Token', 'X-Requested-With'])
    from auth.routes import bp as auth
    from doctor.routes import bp as doctor
    from patient.routes import bp as patient
    from admin.routes import bp as admin
    from superadmin.routes import bp as superadmin
    from patient.child_routes import bp as children
    from vaccination.routes import bp as vaccination
    from patient.adult_routes import bp as adults
    for blueprint in (auth, doctor, patient, admin, superadmin, children, vaccination, adults):
        app.register_blueprint(blueprint)

    @app.before_request
    def guard_cookie_posts():
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and transport() == 'cookie':
            cookie_request_guard()

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/health')
    @app.get('/api/v1/health')
    def health():
        return jsonify(status='ok', service='familycare-backend', auth='flask-jwt')

    @app.get('/api/v1/health/ready')
    def ready():
        db().execute(text('SELECT id FROM familycare.users LIMIT 0'))
        return jsonify(status='ready', database='postgresql')

    from core.openapi import install_docs
    install_docs(app)
    return app
