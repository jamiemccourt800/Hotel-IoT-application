from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory, abort, g
import os
import jwt
from datetime import timedelta, datetime
from datetime import timedelta
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

HOTELS_API_URL = os.getenv('HOTELS_API_URL', 'http://hotels:5001')
USERS_API_URL = os.getenv('USERS_API_URL', 'http://users:5002')
BOOKINGS_API_URL = os.getenv('BOOKINGS_API_URL', 'http://bookings:5003')

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

# Serve shared static files (mounted at /app/static_upstream) at /static/* to match template references
@app.route('/static/<path:filename>', endpoint='static')
def shared_static(filename):
    # Prefer domain-local static if present, then fallback to shared main/static
    local_path = os.path.join(app.root_path, 'static')
    shared_path = os.path.join(app.root_path, 'static_upstream')
    try:
        candidate = os.path.join(local_path, filename)
        if os.path.isfile(candidate):
            return send_from_directory(local_path, filename)
        return send_from_directory(shared_path, filename)
    except Exception:
        abort(404)

def manager_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = session.get('user')
        if not u:
            if _wants_json():
                return jsonify({'ok': False, 'error': 'Auth required'}), 401
            return redirect('/login')
        if u.get('role') not in ('admin','manager'):
            if _wants_json():
                return jsonify({'ok': False, 'error': 'Manager or admin required'}), 403
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper

@app.route('/')
@app.route('/hotels')
def hotels_page():
    return render_template('hotels.html', user=current_user())

@app.route('/hotel/<hotel_id>')
def hotel_detail_page(hotel_id):
    return render_template('hotel_detail.html', user=current_user(), hotel_id=hotel_id)

@app.route('/manage-hotels')
@manager_only
def manage_hotels_page():
    return render_template('manage_hotels.html', user=current_user())

@app.route('/create-hotel')
@manager_only
def create_hotel_page():
    return render_template('create_hotel.html', user=current_user())

@app.route('/edit-hotel/<hotel_id>')
@manager_only
def edit_hotel_page(hotel_id):
    return render_template('edit_hotel.html', user=current_user(), hotel_id=hotel_id)

# Proxy API calls to backend services
@app.route('/api/hotels')
def api_hotels():
    try:
        r = requests.get(f"{HOTELS_API_URL}/api/hotels", params=request.args, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Hotels service unavailable'}), 502

@app.route('/api/hotels/cities')
def api_hotels_cities():
    try:
        r = requests.get(f"{HOTELS_API_URL}/api/hotels/cities", headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Hotels service unavailable'}), 502

@app.route('/api/hotels/create', methods=['POST'])
@manager_only
def api_hotels_create():
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    try:
        r = requests.post(f"{HOTELS_API_URL}/api/hotels/create", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Hotels service unavailable'}), 502

@app.route('/api/hotels/<hotel_id>', methods=['GET','PATCH'])
def api_hotels_detail_update(hotel_id):
    try:
        if request.method == 'GET':
            r = requests.get(f"{HOTELS_API_URL}/api/hotels/{hotel_id}", headers=_forward_auth_headers(), timeout=10)
        else:
            payload = request.get_json(silent=True) or {}
            r = requests.patch(f"{HOTELS_API_URL}/api/hotels/{hotel_id}", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Hotels service unavailable'}), 502

@app.route('/api/hotels/<hotel_id>/managers', methods=['POST','DELETE'])
@manager_only
def api_hotel_managers(hotel_id):
    payload = request.get_json(silent=True) or {}
    try:
        if request.method == 'POST':
            r = requests.post(f"{HOTELS_API_URL}/api/hotels/{hotel_id}/managers", json=payload, headers=_forward_auth_headers(), timeout=10)
        else:
            r = requests.delete(f"{HOTELS_API_URL}/api/hotels/{hotel_id}/managers", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Hotels service unavailable'}), 502

@app.route('/api/hotels/<hotel_id>/visibility', methods=['PATCH'])
@manager_only
def api_hotel_visibility(hotel_id):
    payload = request.get_json(silent=True) or {}
    try:
        r = requests.patch(f"{HOTELS_API_URL}/api/hotels/{hotel_id}/visibility", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Hotels service unavailable'}), 502

# ---- Bookings management proxy (manager/admin) ----
BOOKINGS_API_URL = os.getenv('BOOKINGS_API_URL', 'http://bookings:5003')

@app.route('/api/admin/bookings')
@manager_only
def admin_list_bookings():
    try:
        r = requests.get(f"{BOOKINGS_API_URL}/api/bookings", params=request.args, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502

@app.route('/api/admin/bookings/<booking_id>/status', methods=['PATCH'])
@manager_only
def admin_update_booking_status(booking_id):
    payload = request.get_json(silent=True) or {}
    try:
        r = requests.patch(f"{BOOKINGS_API_URL}/api/bookings/{booking_id}/status", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502

# Availability proxy (used by dashboards and booking UI)
@app.get('/api/availability')
def api_availability():
    try:
        r = requests.get(f"{BOOKINGS_API_URL}/api/availability", params=request.args, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502
    
@app.route('/health')
def health():
    return {'ok': True}

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.pop('user', None)
    if request.method == 'GET':
        return redirect(url_for('hotels_page'))
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)
