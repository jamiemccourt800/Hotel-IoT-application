from flask import Blueprint, request, jsonify
from controllers.auth_controller import *;

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    return jsonify(login_user(data))
