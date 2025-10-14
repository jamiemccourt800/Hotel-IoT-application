from flask import Blueprint, jsonify
from controllers.user_controller import *


userbp = Blueprint('user_bp', __name__, url_prefix='/api/user')

