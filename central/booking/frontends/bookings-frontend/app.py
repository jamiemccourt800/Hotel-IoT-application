from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory, abort, g, Response
import os
from datetime import timedelta, datetime
import jwt
import requests
from functools import wraps
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__, template_folder='templates', static_folder=None)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
# Shared session settings across all frontends so one cookie works everywhere
app.config.update(
    SESSION_COOKIE_NAME=os.getenv('SESSION_COOKIE_NAME', 'booking_session'),
    SESSION_COOKIE_SAMESITE=os.getenv('SESSION_COOKIE_SAMESITE', 'Lax'),
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', '0') in ('1','true','True'),
    PERMANENT_SESSION_LIFETIME=timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', '7'))),
)

JWT_SECRET = os.getenv('JWT_SECRET', app.config['SECRET_KEY'])
JWT_ALGO = os.getenv('JWT_ALGO', 'HS256')
JWT_COOKIE_NAME = os.getenv('JWT_COOKIE_NAME', 'booking_jwt')

def current_user():
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
def _load_user():
    current_user()

# Allow including shared templates from monorepo (mounted at /app/templates_upstream)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(app.root_path, 'templates')),
    FileSystemLoader(os.path.join(app.root_path, 'templates_upstream')),
])

BOOKINGS_API_URL = os.getenv('BOOKINGS_API_URL', 'http://bookings:5003')


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

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            if _wants_json():
                return jsonify({'ok': False, 'error': 'Auth required'}), 401
            return redirect('/login')
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

@app.route('/bookings')
@login_required
def bookings_page():
    # Provide the current user to shared templates (e.g., spanel.html) so the UI reflects login state
    return render_template('bookings/bookings.html', user=current_user())

# Proxy to bookings API
@app.route('/api/bookings', methods=['GET','POST'])
@login_required
def api_bookings_collection():
    try:
        if request.method == 'GET':
            r = requests.get(f"{BOOKINGS_API_URL}/api/bookings", headers=_forward_auth_headers(), timeout=10)
        else:
            payload = request.get_json(silent=True) or request.form.to_dict() or {}
            r = requests.post(f"{BOOKINGS_API_URL}/api/bookings", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502

@app.route('/api/bookings/<booking_id>', methods=['DELETE'])
@login_required
def api_bookings_delete(booking_id):
    try:
        r = requests.delete(f"{BOOKINGS_API_URL}/api/bookings/{booking_id}", headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502
    
@app.route('/api/admin/bookings')
def api_admin_bookings_list():
    """Proxy list bookings for managers/admins (backend enforces role; guests get their own)."""
    try:
        r = requests.get(f"{BOOKINGS_API_URL}/api/bookings", params=request.args, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502

@app.route('/api/admin/bookings/<booking_id>', methods=['DELETE'])
def api_admin_bookings_delete(booking_id):
    """Proxy admin-only hard delete to the bookings backend. Backend enforces admin role via headers."""
    try:
        r = requests.delete(f"{BOOKINGS_API_URL}/api/admin/bookings/{booking_id}", headers=_forward_auth_headers(), timeout=10)
        # Prefer JSON if available; otherwise pass through raw content to preserve status/text
        try:
            data = r.json()
            return jsonify(data), r.status_code
        except ValueError:
            return Response(r.content, status=r.status_code, content_type=r.headers.get('Content-Type', 'application/json'))
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502
    
@app.route('/manage-bookings')
def manage_bookings_page():
    # Template lives under templates/bookings/manage_bookings.html
    return render_template('bookings/manage_bookings.html', user=current_user())

@app.route('/health')
def health():
    return {'ok': True}

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.pop('user', None)
    if request.method == 'GET':
        return redirect('/')
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5300, debug=True)
