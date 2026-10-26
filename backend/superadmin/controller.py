from common.http import body
from flask import g, jsonify
from auth import controller as auth_controller
from common.security import protected
from superadmin import model


def signin():
    return auth_controller.signin(expected_role=model.ROLE)


@protected(model.ROLE)
def me():
    return jsonify(email=g.user['email'], **model.current_profile(g.user['id'], g.token))


@protected('super_admin')
def change_role(user_id):
    data = body()
    if data is None or data.get('role') not in ('patient', 'doctor', 'admin', 'super_admin'):
        return jsonify(error='Valid role required'), 400
    model.set_role(g.token, user_id, data['role'])
    return jsonify(message='Role updated')

