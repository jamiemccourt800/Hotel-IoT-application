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
ROOMS_API_URL = os.getenv('ROOMS_API_URL', 'http://rooms:5001')
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

# ---- Rooms proxy for hotel pages ----
@app.route('/api/rooms', methods=['GET','POST'])
@manager_only
def api_rooms():
    try:
        if request.method == 'GET':
            r = requests.get(f"{ROOMS_API_URL}/api/rooms", params=request.args, headers=_forward_auth_headers(), timeout=10)
        else:
            payload = request.get_json(silent=True) or request.form.to_dict() or {}
            r = requests.post(f"{ROOMS_API_URL}/api/rooms", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Rooms service unavailable'}), 502

@app.route('/api/rooms/<room_id>', methods=['GET','PATCH'])
@manager_only
def api_room_detail_update(room_id):
    try:
        if request.method == 'GET':
            r = requests.get(f"{ROOMS_API_URL}/api/rooms/{room_id}", headers=_forward_auth_headers(), timeout=10)
        else:
            payload = request.get_json(silent=True) or {}
            r = requests.patch(f"{ROOMS_API_URL}/api/rooms/{room_id}", json=payload, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Rooms service unavailable'}), 502

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

@app.route('/api/admin/bookings/<booking_id>', methods=['DELETE'])
@manager_only
def admin_delete_booking(booking_id):
    """Proxy admin hard-delete to bookings service. Only admin should succeed; backend enforces role."""
    try:
        r = requests.delete(f"{BOOKINGS_API_URL}/api/admin/bookings/{booking_id}", headers=_forward_auth_headers(), timeout=10)
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
    
@app.get('/api/availability/rooms')
def api_availability_rooms():
    try:
        r = requests.get(f"{BOOKINGS_API_URL}/api/availability/rooms", params=request.args, headers=_forward_auth_headers(), timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502

@app.get('/api/availability/rooms-grid')
def api_availability_rooms_grid():
    try:
        r = requests.get(f"{BOOKINGS_API_URL}/api/availability/rooms-grid", params=request.args, headers=_forward_auth_headers(), timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({'ok': False, 'error': 'Bookings service unavailable'}), 502

@app.get('/hotel-occupancy/<hotel_id>')
@manager_only
def hotel_occupancy(hotel_id):
    return render_template('hotel_occupancy.html', user=current_user(), hotel_id=hotel_id)
    
@app.route('/health')
def health():
    return {'ok': True}


# --------------------
# Booking.com-compatible mock API (prefix: /booking-com/api)
# This provides a lightweight in-memory mock that other services or tests
# can call as if they were talking to Booking.com. It's intentionally simple
# and not persistent.
# --------------------

from threading import Lock
import uuid

# In-memory stores
_bc_hotels = {}
_bc_bookings = {}
_bc_lock = Lock()

def _seed_booking_com_hotels():
    """Seed a few sample hotels using the hotels proxy if available, otherwise defaults."""
    global _bc_hotels
    try:
        # Try to fetch from the local hotels service to keep data consistent with the app
        r = requests.get(f"{HOTELS_API_URL}/api/hotels", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and data.get('ok') and isinstance(data.get('hotels'), list):
                for h in data.get('hotels')[:10]:
                    _bc_hotels[h.get('id') or str(uuid.uuid4())] = {
                        'hotel_id': h.get('id') or str(uuid.uuid4()),
                        'name': h.get('name'),
                        'city': h.get('city'),
                        'country': h.get('country'),
                        'price': float(h.get('price_per_night') or h.get('price') or 0),
                        'rooms_total': int(h.get('room_count') or 0),
                        'image': h.get('image')
                    }
                return
    except Exception:
        pass

    # Fallback sample data
    sample = [
        {'hotel_id': 'bc-1', 'name': 'Grand Mock Hotel', 'city': 'Dublin', 'country': 'Ireland', 'price': 129.0, 'rooms_total': 120, 'image': ''},
        {'hotel_id': 'bc-2', 'name': 'Mock Inn Central', 'city': 'London', 'country': 'UK', 'price': 99.0, 'rooms_total': 60, 'image': ''},
        {'hotel_id': 'bc-3', 'name': 'Seaside Mock Resort', 'city': 'Barcelona', 'country': 'Spain', 'price': 159.0, 'rooms_total': 200, 'image': ''},
    ]
    for h in sample:
        _bc_hotels[h['hotel_id']] = h


_seed_booking_com_hotels()


@app.route('/booking-com/health')
def booking_com_health():
    return jsonify({'ok': True, 'mock': 'booking-com'})


@app.route('/booking-com/api/hotels', methods=['GET'])
def bc_list_hotels():
    """Return a Booking.com-style list of hotels. Supports ?city= and pagination params."""
    city = request.args.get('city')
    per_page = int(request.args.get('per_page') or request.args.get('limit') or 25)
    page = int(request.args.get('page') or request.args.get('page_no') or 1)
    hotels = list(_bc_hotels.values())
    if city:
        hotels = [h for h in hotels if (h.get('city') or '').lower() == city.lower()]
    start = (page-1)*per_page
    end = start + per_page
    result = {
        'hotels': hotels[start:end],
        'meta': {'page': page, 'per_page': per_page, 'total': len(hotels)}
    }
    return jsonify(result)


@app.route('/booking-com/api/hotels', methods=['POST'])
def bc_create_property():
    """Create a new property following the HDCN-like schema described by the user.

    Required fields: position (latitude, longitude), check_in (from, until), property_name,
    either property_category or booking_property_category, room_count, target, physical_address,
    legal_entity_id.
    """
    payload = request.get_json(silent=True) or {}
    errors = []

    # position
    position = payload.get('position')
    if not position or not isinstance(position, dict):
        errors.append('position.required')
    else:
        lat = position.get('latitude')
        lon = position.get('longitude')
        try:
            lat = float(lat)
            lon = float(lon)
        except Exception:
            errors.append('position.latitude_or_longitude.invalid')

    # check_in
    check_in = payload.get('check_in')
    if not check_in or not isinstance(check_in, dict) or not check_in.get('from'):
        errors.append('check_in.required')

    # property_name
    property_name = payload.get('property_name')
    if not property_name or not isinstance(property_name, str) or len(property_name.strip())==0:
        errors.append('property_name.required')

    # category
    property_category = payload.get('property_category')
    booking_property_category = payload.get('booking_property_category')
    if property_category is None and booking_property_category is None:
        errors.append('category.required')

    # room_count
    room_count = payload.get('room_count')
    try:
        room_count = int(room_count)
        if room_count < 0:
            raise ValueError()
    except Exception:
        errors.append('room_count.invalid')

    # target
    target = payload.get('target')
    if target not in ('test','production'):
        errors.append('target.invalid')

    # physical_address
    physical_address = payload.get('physical_address')
    if not physical_address or not isinstance(physical_address, dict):
        errors.append('physical_address.required')
    else:
        if not physical_address.get('city_name') or not physical_address.get('country_code') or not physical_address.get('address_line'):
            errors.append('physical_address.incomplete')

    # legal_entity_id
    legal_entity_id = payload.get('legal_entity_id')
    try:
        legal_entity_id = int(legal_entity_id)
    except Exception:
        errors.append('legal_entity_id.required_or_invalid')

    if errors:
        return jsonify({'ok': False, 'errors': errors}), 400

    # create id and store
    with _bc_lock:
        new_id = payload.get('provider_property_id') or f"bc-{str(uuid.uuid4())[:8]}"
        # normalize to hotel object shape used elsewhere
        hotel_obj = {
            'hotel_id': new_id,
            'name': property_name,
            'position': {'latitude': float(position.get('latitude')), 'longitude': float(position.get('longitude'))} if position else {},
            'city': physical_address.get('city_name'),
            'country': physical_address.get('country_code'),
            'address': physical_address.get('address_line'),
            'price': float(payload.get('price') or payload.get('price_per_night') or 0),
            'rooms_total': int(room_count),
            'target': target,
            'created_at': datetime.utcnow().isoformat(),
        }
        _bc_hotels[new_id] = hotel_obj

    return jsonify({'ok': True, 'hotel_id': new_id, 'hotel': hotel_obj}), 201


@app.route('/booking-com/api/hotels/<hotel_id>', methods=['GET'])
def bc_hotel_detail(hotel_id):
    h = _bc_hotels.get(hotel_id) or next((v for k,v in _bc_hotels.items() if k==hotel_id or v.get('hotel_id')==hotel_id), None)
    if not h:
        return jsonify({'error': 'not_found'}), 404
    return jsonify(h)


@app.route('/booking-com/api/availability', methods=['GET'])
def bc_availability():
    """Simple availability check: accepts hotel_id, start_date, end_date and returns available rooms count.
    This mock doesn't track detailed per-room bookings; it returns rooms_total minus active bookings in range.
    """
    hotel_id = request.args.get('hotel_id')
    start = request.args.get('start') or request.args.get('start_date')
    end = request.args.get('end') or request.args.get('end_date')
    if not hotel_id or hotel_id not in _bc_hotels:
        return jsonify({'ok': False, 'error': 'hotel_id required or not found'}), 400
    # Count overlapping bookings
    def overlaps(b):
        try:
            bs = datetime.fromisoformat(b['start'])
            be = datetime.fromisoformat(b['end'])
            qs = datetime.fromisoformat(start) if start else None
            qe = datetime.fromisoformat(end) if end else None
            if not qs or not qe: return True
            return not (be <= qs or bs >= qe)
        except Exception:
            return False
    with _bc_lock:
        active = sum(1 for b in _bc_bookings.values() if b.get('hotel_id')==hotel_id and overlaps(b))
        available = max(0, _bc_hotels[hotel_id].get('rooms_total', 0) - active)
    return jsonify({'hotel_id': hotel_id, 'available': available, 'total': _bc_hotels[hotel_id].get('rooms_total', 0)})


@app.route('/booking-com/api/bookings', methods=['POST'])
def bc_create_booking():
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    hotel_id = payload.get('hotel_id')
    guest = payload.get('guest') or payload.get('guest_name')
    start = payload.get('start') or payload.get('start_date')
    end = payload.get('end') or payload.get('end_date')
    if not hotel_id or not guest or not start or not end:
        return jsonify({'ok': False, 'error': 'missing_fields'}), 400
    if hotel_id not in _bc_hotels:
        return jsonify({'ok': False, 'error': 'hotel_not_found'}), 404
    # naive availability check
    with _bc_lock:
        bid = str(uuid.uuid4())
        _bc_bookings[bid] = {'booking_id': bid, 'hotel_id': hotel_id, 'guest': guest, 'start': start, 'end': end, 'status': 'confirmed', 'created_at': datetime.utcnow().isoformat()}
    return jsonify({'ok': True, 'booking_id': bid, 'status': 'confirmed'})


@app.route('/booking-com/api/bookings/<booking_id>', methods=['GET','DELETE','PATCH'])
def bc_booking_detail(booking_id):
    b = _bc_bookings.get(booking_id)
    if not b:
        return jsonify({'ok': False, 'error': 'not_found'}), 404
    if request.method == 'GET':
        return jsonify(b)
    if request.method == 'DELETE':
        with _bc_lock:
            _bc_bookings.pop(booking_id, None)
        return jsonify({'ok': True})
    if request.method == 'PATCH':
        payload = request.get_json(silent=True) or {}
        with _bc_lock:
            b.update(payload)
        return jsonify({'ok': True, 'booking': b})


@app.route('/booking-com/debug')
def booking_com_debug():
    return jsonify({'hotels': len(_bc_hotels), 'bookings': len(_bc_bookings)})

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.pop('user', None)
    if request.method == 'GET':
        return redirect(url_for('hotels_page'))
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)
