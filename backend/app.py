from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from common.errors import register_errors


def create_app():
    load_dotenv(Path(__file__).with_name('.env'))
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=16384)
    register_errors(app)
    from auth.routes import bp as auth
    from doctor.routes import bp as doctor
    from patient.routes import bp as patient
    from admin.routes import bp as admin
    from superadmin.routes import bp as superadmin
    for blueprint in (auth, doctor, patient, admin, superadmin):
        app.register_blueprint(blueprint)

    @app.get('/health')
    def health():
        return jsonify(status='ok', service='familycare-backend')

    return app


app = create_app()
