from flask import g, jsonify
from auth import controller as auth_controller
from common.security import protected
from doctor import model


def signin():
    return auth_controller.signin(expected_role=model.ROLE)


@protected(model.ROLE)
def me():
    return jsonify(email=g.user['email'], **model.current_profile(g.user['id'], g.token))


def signup():
    return auth_controller.signup(role_override=model.ROLE)
