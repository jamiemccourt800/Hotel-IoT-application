from flask import Flask, jsonify, request
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import time
from math import ceil

app = Flask(__name__)

MONGO_HOST = os.getenv("MONGO_HOST", "mongodb") or "mongodb"
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "bookings")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}" if MONGO_USER and MONGO_PASS else f"mongodb://{MONGO_HOST}:{MONGO_PORT}"
client = MongoClient(uri)
db = client[MONGO_DB]

ROLE_HIERARCHY = {'admin': 3, 'manager': 2, 'guest': 1}

def actor():
    username = (request.headers.get('X-User-Name') or '').strip()
    role = (request.headers.get('X-User-Role') or 'guest').strip().lower()
    role = role if role in ROLE_HIERARCHY else 'guest'
    return {'username': username or None, 'role': role}

# ---- Availability helpers ----
def _parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return None

def _date_iter(start_date, end_date):
    """Yield dates from start (inclusive) to end (exclusive)."""
    cur = start_date
    while cur < end_date:
        yield cur
        cur = cur + timedelta(days=1)

def _rooms_needed(guests: int) -> int:
    try:
        g = int(guests)
        return max(1, ceil(g / 2))
    except Exception:
        return 1

@app.post('/api/bookings')
def create_booking():
    a = actor()
    if not a.get('username'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    data = request.get_json(silent=True) or {}
    hotel_id = (data.get('hotel_id') or '').strip()
    check_in = (data.get('check_in') or '').strip()
    check_out = (data.get('check_out') or '').strip()
    guests_raw = data.get('guests', 1)
    try:
        guests = int(guests_raw)
        if guests < 1:
            raise ValueError('guests')
    except Exception:
        return jsonify({'ok': False, 'error': 'guests must be positive integer'}), 400
    if not hotel_id or not check_in or not check_out:
        return jsonify({'ok': False, 'error': 'hotel_id, check_in, check_out required'}), 400
    try:
        ci_dt = datetime.strptime(check_in, '%Y-%m-%d')
        co_dt = datetime.strptime(check_out, '%Y-%m-%d')
    except ValueError:
        return jsonify({'ok': False, 'error': 'Invalid date format (YYYY-MM-DD)'}), 400
    if co_dt <= ci_dt:
        return jsonify({'ok': False, 'error': 'check_out must be after check_in'}), 400
    from bson import ObjectId
    try:
        oid = ObjectId(hotel_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid hotel id'}), 400
    hotel = db.hotels.find_one({'_id': oid})
    if not hotel:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    nights = (co_dt - ci_dt).days
    nightly = hotel.get('price_per_night', 0)
    try:
        nightly_float = float(nightly)
    except Exception:
        nightly_float = 0.0
    total_cost = nightly_float * nights

    # Prevent overbooking: consider confirmed bookings only and 1-2 guests per room.
    room_count = int(hotel.get('room_count') or 0)
    if room_count <= 0:
        return jsonify({'ok': False, 'error': 'No rooms available for this hotel'}), 409
    rooms_req = _rooms_needed(guests)
    start_str = ci_dt.strftime('%Y-%m-%d')
    end_str = co_dt.strftime('%Y-%m-%d')
    q = {
        'hotel_id': hotel_id,
        'status': 'confirmed',
        'check_in': {'$lt': end_str},
        'check_out': {'$gt': start_str},
    }
    overlaps = list(db.bookings.find(q, {'check_in': 1, 'check_out': 1, 'guests': 1, '_id': 0}))
    per_day = {}
    for b in overlaps:
        b_ci = _parse_date(b.get('check_in') or '')
        b_co = _parse_date(b.get('check_out') or '')
        if not b_ci or not b_co or b_co <= b_ci:
            continue
        s_i = max(ci_dt.date(), b_ci)
        e_i = min(co_dt.date(), b_co)
        if e_i <= s_i:
            continue
        rn = _rooms_needed(b.get('guests') or 1)
        for d in _date_iter(s_i, e_i):
            key = d.strftime('%Y-%m-%d')
            per_day[key] = per_day.get(key, 0) + rn
    # Check capacity for each day in requested stay
    for d in _date_iter(ci_dt.date(), co_dt.date()):
        key = d.strftime('%Y-%m-%d')
        if per_day.get(key, 0) + rooms_req > room_count:
            return jsonify({'ok': False, 'error': 'Selected dates are fully booked'}), 409
    booking = {
        'hotel_id': hotel_id,
        'hotel_name': hotel.get('name'),
        'username': a.get('username'),
        'display_name': None,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'guests': guests,
        'price_per_night': nightly_float,
        'total_cost': total_cost,
        'created_at': int(time.time()),
        'status': 'pending'
    }
    res = db.bookings.insert_one(booking)
    try:
        # Ensure ObjectId is serializable in response
        booking['_id'] = str(res.inserted_id)
    except Exception:
        # Fallback: omit _id if something unexpected occurs
        booking.pop('_id', None)
    return jsonify({'ok': True, 'booking': booking}), 201

@app.get('/api/availability')
def availability():
    """Return per-day booked and available rooms for a hotel in [start, end)."""
    hotel_id = (request.args.get('hotel_id') or '').strip()
    start = (request.args.get('start') or '').strip()
    end = (request.args.get('end') or '').strip()
    if not hotel_id or not start or not end:
        return jsonify({'ok': False, 'error': 'hotel_id, start, end required'}), 400
    s = _parse_date(start)
    e = _parse_date(end)
    if not s or not e:
        return jsonify({'ok': False, 'error': 'Invalid date format (YYYY-MM-DD)'}), 400
    if e <= s:
        return jsonify({'ok': False, 'error': 'end must be after start'}), 400
    # Load hotel to get room_count
    from bson import ObjectId
    try:
        ho = db.hotels.find_one({'_id': ObjectId(hotel_id)})
    except Exception:
        ho = None
    if not ho:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    room_count = int(ho.get('room_count') or 0)
    # Overlapping confirmed bookings
    q = {
        'hotel_id': hotel_id,
        'status': 'confirmed',
        'check_in': {'$lt': end},
        'check_out': {'$gt': start},
    }
    overlaps = list(db.bookings.find(q, {'check_in': 1, 'check_out': 1, 'guests': 1, '_id': 0}))
    per_day = {}
    for b in overlaps:
        b_ci = _parse_date(b.get('check_in') or '')
        b_co = _parse_date(b.get('check_out') or '')
        if not b_ci or not b_co or b_co <= b_ci:
            continue
        s_i = max(s, b_ci)
        e_i = min(e, b_co)
        if e_i <= s_i:
            continue
        rn = _rooms_needed(b.get('guests') or 1)
        for d in _date_iter(s_i, e_i):
            key = d.strftime('%Y-%m-%d')
            per_day[key] = per_day.get(key, 0) + rn
    days = []
    max_booked = 0
    min_avail = None
    fully = []
    for d in _date_iter(s, e):
        key = d.strftime('%Y-%m-%d')
        booked = int(per_day.get(key, 0))
        avail = max(0, room_count - booked)
        days.append({'date': key, 'booked_rooms': booked, 'available_rooms': avail})
        if booked > max_booked:
            max_booked = booked
        if min_avail is None or avail < min_avail:
            min_avail = avail
        if avail <= 0:
            fully.append(key)
    return jsonify({
        'ok': True,
        'hotel_id': hotel_id,
        'room_count': room_count,
        'start': start,
        'end': end,
        'max_booked': max_booked,
        'min_available': (min_avail if min_avail is not None else room_count),
        'fully_booked_dates': fully,
        'days': days,
    })

@app.get('/api/bookings')
def list_bookings():
    a = actor()
    if not a.get('username'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    role = a.get('role')
    username_filter = (request.args.get('user') or '').strip()
    hotel_id = (request.args.get('hotel_id') or '').strip()
    q = {}
    if role == 'admin':
        if username_filter:
            q['username'] = username_filter
        if hotel_id:
            q['hotel_id'] = hotel_id
    elif role == 'manager':
        # Limit to hotels managed by this manager
        managed_ids = []
        try:
            for h in db.hotels.find({'managers': {'$in': [a.get('username')]}}):
                try:
                    managed_ids.append(str(h.get('_id')))
                except Exception:
                    pass
        except Exception:
            managed_ids = []
        if not managed_ids:
            return jsonify({'ok': True, 'bookings': []})
        if hotel_id:
            if hotel_id not in managed_ids:
                return jsonify({'ok': True, 'bookings': []})
            q['hotel_id'] = hotel_id
        else:
            q['hotel_id'] = {'$in': managed_ids}
        if username_filter:
            q['username'] = username_filter
    else:
        q['username'] = a.get('username')
    status = (request.args.get('status') or '').strip().lower()
    if status in ('pending','confirmed','cancelled','denied'):
        q['status'] = status
    docs = []
    for b in db.bookings.find(q).sort('created_at', -1).limit(500):
        b['_id'] = str(b['_id'])
        docs.append(b)
    return jsonify({'ok': True, 'bookings': docs})

@app.patch('/api/bookings/<booking_id>/status')
def update_booking_status(booking_id):
    a = actor()
    if not a.get('username'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    if a.get('role') not in ('manager','admin'):
        return jsonify({'ok': False, 'error': 'Manager or admin required'}), 403
    from bson import ObjectId
    try:
        oid = ObjectId(booking_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid booking id'}), 400
    # Enforce manager scoping to their hotels
    booking = db.bookings.find_one({'_id': oid})
    if not booking:
        return jsonify({'ok': False, 'error': 'Booking not found'}), 404
    if a.get('role') == 'manager':
        hid = booking.get('hotel_id')
        allowed = False
        try:
            from bson import ObjectId as _OID
            ho = db.hotels.find_one({'_id': _OID(hid)})
            if ho and a.get('username') in (ho.get('managers') or []):
                allowed = True
        except Exception:
            allowed = False
        if not allowed:
            return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    payload = request.get_json(silent=True) or {}
    new_status = (payload.get('status') or '').strip().lower()
    if new_status not in ('confirmed','denied','cancelled'):
        return jsonify({'ok': False, 'error': 'Invalid status'}), 400
    updates = {'status': new_status, 'updated_at': int(time.time())}
    note = (payload.get('note') or '').strip()
    if note:
        updates['manager_note'] = note
    res = db.bookings.update_one({'_id': oid}, {'$set': updates})
    if res.matched_count == 0:
        return jsonify({'ok': False, 'error': 'Booking not found'}), 404
    b = db.bookings.find_one({'_id': oid})
    if not b:
        return jsonify({'ok': False, 'error': 'Booking not found'}), 404
    b['_id'] = str(b['_id'])
    return jsonify({'ok': True, 'booking': b})

@app.delete('/api/bookings/<booking_id>')
def cancel_booking(booking_id):
    a = actor()
    if not a.get('username'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    from bson import ObjectId
    try:
        oid = ObjectId(booking_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid booking id'}), 400
    booking = db.bookings.find_one({'_id': oid})
    if not booking:
        return jsonify({'ok': False, 'error': 'Booking not found'}), 404
    if booking.get('username') != a.get('username'):
        role = a.get('role')
        if role == 'admin':
            pass
        elif role == 'manager':
            hid = booking.get('hotel_id')
            allowed = False
            try:
                from bson import ObjectId as _OID
                ho = db.hotels.find_one({'_id': _OID(hid)})
                if ho and a.get('username') in (ho.get('managers') or []):
                    allowed = True
            except Exception:
                allowed = False
            if not allowed:
                return jsonify({'ok': False, 'error': 'Not authorized'}), 403
        else:
            return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    if booking.get('status') != 'cancelled':
        db.bookings.update_one({'_id': oid}, {'$set': {'status': 'cancelled', 'cancelled_at': int(time.time())}})
    return jsonify({'ok': True, 'booking_id': booking_id, 'status': 'cancelled'})

@app.get('/health')
def health():
    try:
        client.admin.command('ping')
        return {"ok": True, "mongo": "up"}
    except Exception as e:
        return {"ok": False, "mongo": "error", "error": str(e)}, 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5003'))
    app.run(host='0.0.0.0', port=port, debug=True)
