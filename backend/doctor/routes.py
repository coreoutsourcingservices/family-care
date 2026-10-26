from flask import Blueprint
from doctor import controller

bp = Blueprint('doctor', __name__, url_prefix='/api/doctor')
bp.add_url_rule('/signin', view_func=controller.signin, methods=['POST'])
bp.add_url_rule('/me', view_func=controller.me, methods=['GET'])
bp.add_url_rule('/signup', view_func=controller.signup, methods=['POST'])
