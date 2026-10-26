from flask import g, jsonify, request
from auth import controller as auth_controller
from common.security import protected
from admin import model


def signin():
    return auth_controller.signin(expected_role=model.ROLE)


@protected(model.ROLE)
def me():
    return jsonify(email=g.user['email'], **model.current_profile(g.user['id'], g.token))


@protected('admin', 'super_admin')
def users():
    try:
        offset = max(0, int(request.args.get('offset', 0)))
    except ValueError:
        return jsonify(error='offset must be an integer'), 400
    return jsonify(model.list_users(g.token, offset))

