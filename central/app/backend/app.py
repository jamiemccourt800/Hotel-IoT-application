from flask import Flask
from routes.auth_routes import auth_bp


app = Flask(__name__)


auth_bp.register_blueprint(auth_bp)

if(__name__ == '__main__'):
    app.run(debug=True, host='0.0.0.0', port=5000)