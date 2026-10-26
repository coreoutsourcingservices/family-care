from flask import Blueprint
from patient import controller

bp = Blueprint('patient', __name__, url_prefix='/api/patient')
bp.add_url_rule('/signin', view_func=controller.signin, methods=['POST'])
bp.add_url_rule('/me', view_func=controller.me, methods=['GET'])
bp.add_url_rule('/signup', view_func=controller.signup, methods=['POST'])
