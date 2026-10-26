from flask import Blueprint
from auth import controller

bp = Blueprint('auth', __name__, url_prefix='/api/auth')
bp.add_url_rule('/signup', view_func=controller.signup, methods=['POST'])
bp.add_url_rule('/signin', view_func=controller.signin, methods=['POST'])
bp.add_url_rule('/refresh', view_func=controller.refresh, methods=['POST'])
bp.add_url_rule('/signout', view_func=controller.signout, methods=['POST'])
bp.add_url_rule('/me', view_func=controller.me, methods=['GET'])
