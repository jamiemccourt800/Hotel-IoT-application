from flask import Flask
import requests
import jsonify


auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')
def login_user(data):
    username = data.get('username')
    password = data.get('password')

    payload = {
        'username': username,
        'password': password
    }
    res = requests.post('http://users:5002/login', json=payload)
    return jsonify(res.json()), res.status_code