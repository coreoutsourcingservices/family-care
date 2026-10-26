from flask import request

def body():
    data = request.get_json()
    if not isinstance(data, dict):
        return None
    return data

