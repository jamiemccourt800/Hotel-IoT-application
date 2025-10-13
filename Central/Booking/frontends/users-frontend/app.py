from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory, abort, g
import os
from datetime import timedelta
import requests
from functools import wraps
from jinja2 import ChoiceLoader, FileSystemLoader
import jwt
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates', static_folder=None)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
# Shared session settings across all frontends so one cookie works everywhere
app.config.update(
    SESSION_COOKIE_NAME=os.getenv('SESSION_COOKIE_NAME', 'booking_session'),
    SESSION_COOKIE_SAMESITE=os.getenv('SESSION_COOKIE_SAMESITE', 'Lax'),
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', '0') in ('1','true','True'),
    PERMANENT_SESSION_LIFETIME=timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', '7'))),
)

# JWT settings
JWT_SECRET = os.getenv('JWT_SECRET', app.config['SECRET_KEY'])
JWT_ALGO = os.getenv('JWT_ALGO', 'HS256')
JWT_COOKIE_NAME = os.getenv('JWT_COOKIE_NAME', 'booking_jwt')
JWT_LIFETIME_MIN = int(os.getenv('JWT_LIFETIME_MIN', '10080'))  # 7 days

def _issue_jwt(user: dict) -> str:
    now = datetime.utcnow()
    payload = {
        'sub': user.get('username'),
        'username': user.get('username'),
        'display_name': user.get('display_name') or user.get('username'),
        'role': user.get('role') or 'guest',
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=JWT_LIFETIME_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def _set_jwt_cookie(resp, token: str):
    resp.set_cookie(
        JWT_COOKIE_NAME,
        token,
        max_age=JWT_LIFETIME_MIN * 60,
        httponly=True,
        secure=app.config.get('SESSION_COOKIE_SECURE', False),
        samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
        path='/'
    )
    return resp

def _clear_jwt_cookie(resp):
    resp.delete_cookie(JWT_COOKIE_NAME, path='/')
    return resp

def current_user() -> dict | None:
    if hasattr(g, 'user'):
        return g.user
    token = request.cookies.get(JWT_COOKIE_NAME)
    if not token:
        g.user = None
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        g.user = {
            'username': payload.get('username') or payload.get('sub'),
            'display_name': payload.get('display_name') or payload.get('username'),
            'role': payload.get('role') or 'guest'
        }
    except Exception:
        g.user = None
    return g.user

@app.before_request
def _load_user_from_jwt():
    current_user()

# Allow including shared templates from monorepo (mounted at /app/templates_upstream)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(app.root_path, 'templates')),
    FileSystemLoader(os.path.join(app.root_path, 'templates_upstream')),
])

USERS_API_URL = os.getenv('USERS_API_URL', 'http://users:5002')

ROLE_HIERARCHY = {'admin':3,'manager':2,'guest':1}

def _forward_auth_headers():
    u = current_user() or {}
    return {'X-User-Name': u.get('username',''), 'X-User-Role': u.get('role','guest')}

def _wants_json():
    return (
        request.args.get('ajax') == '1'
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in (request.headers.get('Accept') or '').lower()
        or request.is_json
    )

def manager_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            if _wants_json():
                return jsonify({'ok': False, 'error': 'Auth required'}), 401
            return redirect(url_for('login_page'))
        if u.get('role') not in ('admin','manager'):
            if _wants_json():
                return jsonify({'ok': False, 'error': 'Manager or admin required'}), 403
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return wrapper

# Serve shared static files (mounted at /app/static_upstream) at /static/* to match template references
@app.route('/static/<path:filename>', endpoint='static')
def shared_static(filename):
    local_path = os.path.join(app.root_path, 'static')
    shared_path = os.path.join(app.root_path, 'static_upstream')
    try:
        candidate = os.path.join(local_path, filename)
        if os.path.isfile(candidate):
            return send_from_directory(local_path, filename)
        return send_from_directory(shared_path, filename)
    except Exception:
        abort(404)

@app.route('/login', methods=['GET','POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.get_json(silent=True)
    # Support form posts too
    if not data:
        data = {
            'username': request.form.get('username','').strip(),
            'password': request.form.get('password','')
        }
    try:
        r = requests.post(f"{USERS_API_URL}/api/auth/login", json=data, timeout=10)
        payload = r.json() if r.headers.get('Content-Type','').lower().startswith('application/json') else {'ok': False}
        if r.status_code == 200 and payload.get('ok'):
            # Set session + JWT cookie
            session.permanent = True
            session['user'] = payload['user']
            token = _issue_jwt(payload['user'])
            if request.headers.get('Accept','').lower().find('application/json') >= 0 or request.args.get('ajax') == '1' or request.is_json:
                resp = jsonify({'ok': True, 'user': payload['user']})
                return _set_jwt_cookie(resp, token)
            # HTML form flow
            resp = redirect('/')
            return _set_jwt_cookie(resp, token)
        # Error
        msg = payload.get('error','Invalid credentials')
        if request.headers.get('Accept','').lower().find('application/json') >= 0 or request.args.get('ajax') == '1' or request.is_json:
            return jsonify({'ok': False, 'error': msg}), r.status_code
        return render_template('login.html', error=msg), r.status_code
    except Exception:
        if request.headers.get('Accept','').lower().find('application/json') >= 0 or request.args.get('ajax') == '1' or request.is_json:
            return jsonify({'ok': False, 'error': 'Auth service unavailable'}), 502
        return render_template('login.html', error='Auth service unavailable'), 502

@app.route('/signup', methods=['GET','POST'])
def signup_page():
    if request.method == 'GET':
        return render_template('signup.html')
    data = request.get_json(silent=True)
    if not data:
        data = {
            'username': request.form.get('username','').strip(),
            'password': request.form.get('password',''),
            'display_name': request.form.get('display_name','').strip() or None
        }
    try:
        r = requests.post(f"{USERS_API_URL}/api/auth/signup", json=data, timeout=10)
        payload = r.json() if r.headers.get('Content-Type','').lower().startswith('application/json') else {'ok': False}
        if r.status_code in (200,201) and payload.get('ok'):
            session.permanent = True
            session['user'] = payload['user']
            token = _issue_jwt(payload['user'])
            if request.headers.get('Accept','').lower().find('application/json') >= 0 or request.args.get('ajax') == '1' or request.is_json:
                resp = jsonify({'ok': True, 'user': payload['user']})
                resp.status_code = 201
                return _set_jwt_cookie(resp, token)
            resp = redirect('/')
            return _set_jwt_cookie(resp, token)
        msg = payload.get('error','Signup failed')
        if request.headers.get('Accept','').lower().find('application/json') >= 0 or request.args.get('ajax') == '1' or request.is_json:
            return jsonify({'ok': False, 'error': msg}), r.status_code
        return render_template('signup.html', error=msg), r.status_code
    except Exception:
        if request.headers.get('Accept','').lower().find('application/json') >= 0 or request.args.get('ajax') == '1' or request.is_json:
            return jsonify({'ok': False, 'error': 'Auth service unavailable'}), 502
        return render_template('signup.html', error='Auth service unavailable'), 502

@app.route('/users')
@manager_only
def users_page():
    u = current_user() or {}
    can_create_admin = u.get('role') == 'admin'
    allowed_roles = ['guest','manager'] + (['admin'] if can_create_admin else [])
    return render_template('users.html', user=u, allowed_roles=allowed_roles)

# Proxy to users API
@app.route('/api/users', methods=['GET','POST'])
@manager_only
def api_users_collection():
    try:
        if request.method == 'GET':
            r = requests.get(f"{USERS_API_URL}/api/users", headers=_forward_auth_headers(), timeout=10)
        else:
            payload = request.get_json(silent=True) or request.form.to_dict() or {}
            r = requests.post(f"{USERS_API_URL}/api/users", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Users service unavailable'}), 502

@app.route('/api/users/create', methods=['POST'])
@manager_only
def api_users_create():
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        r = requests.post(f"{USERS_API_URL}/api/users/create", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Users service unavailable'}), 502

@app.route('/api/users/<username>', methods=['GET','PATCH','DELETE'])
@manager_only
def api_users_update_delete(username):
    try:
        method = request.method
        # Support method override via query or header to be resilient to accidental GETs
        override = (request.args.get('_method') or request.headers.get('X-HTTP-Method-Override') or '').upper()
        if method == 'GET' and override in ('DELETE','PATCH'):
            method = override

        if method == 'PATCH':
            payload = request.get_json(silent=True) or {}
            r = requests.patch(f"{USERS_API_URL}/api/users/{username}", json=payload, headers=_forward_auth_headers(), timeout=10)
            return jsonify(r.json()), r.status_code
        if method == 'DELETE':
            r = requests.delete(f"{USERS_API_URL}/api/users/{username}", headers=_forward_auth_headers(), timeout=10)
            return jsonify(r.json()), r.status_code

        # Unsupported method on this endpoint
        return jsonify({'ok': False, 'error': 'Method not allowed. Use PATCH or DELETE.'}), 405
    except Exception:
        return jsonify({'ok': False, 'error': 'Users service unavailable'}), 502

@app.route('/api/users/<username>/password-change', methods=['POST'])
@manager_only
def api_users_password_change(username):
    payload = request.get_json(silent=True) or {}
    try:
        r = requests.post(f"{USERS_API_URL}/api/users/{username}/password-change", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Users service unavailable'}), 502

@app.route('/health')
def health():
    return {'ok': True}

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.pop('user', None)
    if request.method == 'GET':
        resp = redirect(url_for('login_page'))
        return _clear_jwt_cookie(resp)
    resp = jsonify({'ok': True})
    return _clear_jwt_cookie(resp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5200, debug=True)
