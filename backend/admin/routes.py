from flask import Blueprint
from admin import controller

bp = Blueprint('admin', __name__, url_prefix='/api/admin')
bp.add_url_rule('/signin', view_func=controller.signin, methods=['POST'])
bp.add_url_rule('/me', view_func=controller.me, methods=['GET'])
bp.add_url_rule('/users', view_func=controller.users, methods=['GET'])

# Compatibility with the original role-management URL.
from superadmin.controller import change_role
bp.add_url_rule('/users/<uuid:user_id>/role', view_func=change_role, methods=['PATCH'])
