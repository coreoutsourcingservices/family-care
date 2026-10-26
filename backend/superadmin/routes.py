from flask import Blueprint
from superadmin import controller

bp = Blueprint('superadmin', __name__, url_prefix='/api/superadmin')
bp.add_url_rule('/signin', view_func=controller.signin, methods=['POST'])
bp.add_url_rule('/me', view_func=controller.me, methods=['GET'])
bp.add_url_rule('/users/<uuid:user_id>/role', view_func=controller.change_role, methods=['PATCH'])
