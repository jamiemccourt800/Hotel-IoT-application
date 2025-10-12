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
    room_id_raw = (data.get('room_id') or '').strip()
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

    # If a specific room is requested, enforce that it belongs to the hotel and is not booked.
    start_str = ci_dt.strftime('%Y-%m-%d')
    end_str = co_dt.strftime('%Y-%m-%d')
    room_summary = {}
    if room_id_raw:
        try:
            from bson import ObjectId as _OID
            rid = _OID(room_id_raw)
        except Exception:
            return jsonify({'ok': False, 'error': 'Invalid room id'}), 400
        room = db.rooms.find_one({'_id': rid})
        if not room:
            return jsonify({'ok': False, 'error': 'Room not found'}), 404
        # Ensure room belongs to the same hotel
        try:
            room_hotel_id = str(room.get('hotel_id'))
        except Exception:
            room_hotel_id = None
        if room_hotel_id != hotel_id:
            return jsonify({'ok': False, 'error': 'Room does not belong to this hotel'}), 400
        # Check overlapping confirmed bookings for this room
        q_room = {
            'hotel_id': hotel_id,
            'room_id': room_id_raw,
            'status': 'confirmed',
            'check_in': {'$lt': end_str},
            'check_out': {'$gt': start_str},
        }
        if db.bookings.find_one(q_room, {'_id': 1}):
            return jsonify({'ok': False, 'error': 'Selected room is not available for these dates'}), 409
        # Save a small summary to embed in booking for convenience
        room_summary = {
            'room_id': room_id_raw,
            'room_number': room.get('room_number'),
            'room_type': room.get('type'),
        }
    else:
        # Validate using real per-room availability: find any room with no overlapping
        # confirmed booking for the entire date range, then auto-assign it.
        try:
            from bson import ObjectId as _OID
            hotel_oid = _OID(hotel_id)
        except Exception:
            return jsonify({'ok': False, 'error': 'Invalid hotel id'}), 400

        # Fetch all rooms for this hotel
        room_fields = {'_id': 1, 'room_number': 1, 'type': 1, 'capacity': 1}
        room_docs = list(db.rooms.find({'hotel_id': hotel_oid}, room_fields))
        if not room_docs:
            return jsonify({'ok': False, 'error': 'No rooms available for this hotel'}), 409

        # Gather room_ids that are taken for the overlapping range
        q_room_overlap = {
            'hotel_id': hotel_id,
            'room_id': {'$exists': True, '$ne': ''},
            'status': 'confirmed',
            'check_in': {'$lt': end_str},
            'check_out': {'$gt': start_str},
        }
        taken = set()
        for rb in db.bookings.find(q_room_overlap, {'room_id': 1}):
            rid = rb.get('room_id')
            if rid:
                taken.add(str(rid))

        # Optionally respect room capacity when it's defined
        def can_fit(room):
            try:
                cap = int(room.get('capacity')) if room.get('capacity') is not None else None
            except Exception:
                cap = None
            return (cap is None) or (cap >= guests)

        available = [r for r in room_docs if str(r.get('_id')) not in taken and can_fit(r)]
        if not available:
            return jsonify({'ok': False, 'error': 'Selected dates are fully booked'}), 409

        chosen = available[0]
        room_summary = {
            'room_id': str(chosen.get('_id')),
            'room_number': chosen.get('room_number'),
            'room_type': chosen.get('type')
        }
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
    if room_summary:
        booking.update(room_summary)
    res = db.bookings.insert_one(booking)
    try:
        # Ensure ObjectId is serializable in response
        booking['_id'] = str(res.inserted_id)
    except Exception:
        # Fallback: omit _id if something unexpected occurs
        booking.pop('_id', None)
    return jsonify({'ok': True, 'booking': booking}), 201

@app.get('/api/availability/rooms')
def availability_rooms():
    """Return list of rooms for a hotel that are fully available in [start, end)."""
    hotel_id = (request.args.get('hotel_id') or '').strip()
    start = (request.args.get('start') or '').strip()
    end = (request.args.get('end') or '').strip()
    if not hotel_id or not start or not end:
        return jsonify({'ok': False, 'error': 'hotel_id, start, end required'}), 400
    s = _parse_date(start)
    e = _parse_date(end)
    if not s or not e or e <= s:
        return jsonify({'ok': False, 'error': 'Invalid date range'}), 400
    # Validate hotel exists
    from bson import ObjectId
    try:
        ho = db.hotels.find_one({'_id': ObjectId(hotel_id)})
    except Exception:
        ho = None
    if not ho:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    # Get hotel rooms
    rooms = list(db.rooms.find({'hotel_id': ObjectId(hotel_id)}))
    # Find overlapping confirmed bookings that specify a room_id
    q = {
        'hotel_id': hotel_id,
        'room_id': {'$exists': True, '$ne': ''},
        'status': 'confirmed',
        'check_in': {'$lt': end},
        'check_out': {'$gt': start},
    }
    overlaps = set()
    for b in db.bookings.find(q, {'room_id': 1}):
        rid = b.get('room_id')
        if rid:
            overlaps.add(str(rid))
    out = []
    for r in rooms:
        rid = str(r.get('_id'))
        if rid in overlaps:
            continue
        out.append({
            '_id': rid,
            'room_number': r.get('room_number'),
            'type': r.get('type'),
            'capacity': r.get('capacity'),
            'price_per_night': r.get('price_per_night'),
        })
    return jsonify({'ok': True, 'hotel_id': hotel_id, 'start': start, 'end': end, 'available_rooms': out, 'count': len(out)})

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
    # Load hotel and derive room_count from actual rooms when possible
    from bson import ObjectId
    try:
        ho = db.hotels.find_one({'_id': ObjectId(hotel_id)})
    except Exception:
        ho = None
    if not ho:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    # Prefer actual room list over hotel.room_count for accurate availability
    try:
        rooms = list(db.rooms.find({'hotel_id': ObjectId(hotel_id)}, {'_id': 1}))
    except Exception:
        rooms = []
    room_ids = [str(r['_id']) for r in rooms]
    room_count = len(room_ids)
    if room_count <= 0:
        # Fallback to declared count if no room docs exist
        room_count = int(ho.get('room_count') or 0)

    # Overlapping confirmed bookings in the range
    q = {
        'hotel_id': hotel_id,
        'status': 'confirmed',
        'check_in': {'$lt': end},
        'check_out': {'$gt': start},
    }
    overlaps = list(db.bookings.find(q, {'check_in': 1, 'check_out': 1, 'guests': 1, 'room_id': 1, '_id': 0}))

    # Build per-day booked counts using unique room_ids when present; fall back to
    # estimated rooms-needed only for legacy bookings without room_id.
    booked_sets = {}
    extra_counts = {}
    for b in overlaps:
        b_ci = _parse_date(b.get('check_in') or '')
        b_co = _parse_date(b.get('check_out') or '')
        if not b_ci or not b_co or b_co <= b_ci:
            continue
        s_i = max(s, b_ci)
        e_i = min(e, b_co)
        if e_i <= s_i:
            continue
        rid = (b.get('room_id') or '').strip()
        if rid:
            for d in _date_iter(s_i, e_i):
                key = d.strftime('%Y-%m-%d')
                if key not in booked_sets:
                    booked_sets[key] = set()
                booked_sets[key].add(str(rid))
        else:
            rn = _rooms_needed(b.get('guests') or 1)
            for d in _date_iter(s_i, e_i):
                key = d.strftime('%Y-%m-%d')
                extra_counts[key] = extra_counts.get(key, 0) + rn
    days = []
    max_booked = 0
    min_avail = None
    fully = []
    for d in _date_iter(s, e):
        key = d.strftime('%Y-%m-%d')
        booked_unique = len(booked_sets.get(key, set()))
        booked_extra = int(extra_counts.get(key, 0))
        booked = booked_unique + booked_extra
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

@app.get('/api/availability/rooms-grid')
def availability_rooms_grid():
    """Return a simple room-by-day occupancy grid for managers/admins.
    A cell is True if booked (confirmed booking overlaps), else False.
    """
    a = actor()
    if a.get('role') not in ('manager','admin'):
        return jsonify({'ok': False, 'error': 'Manager or admin required'}), 403
    hotel_id = (request.args.get('hotel_id') or '').strip()
    start = (request.args.get('start') or '').strip()
    end = (request.args.get('end') or '').strip()
    if not hotel_id or not start or not end:
        return jsonify({'ok': False, 'error': 'hotel_id, start, end required'}), 400
    s = _parse_date(start)
    e = _parse_date(end)
    if not s or not e or e <= s:
        return jsonify({'ok': False, 'error': 'Invalid date range'}), 400
    from bson import ObjectId
    try:
        ho = db.hotels.find_one({'_id': ObjectId(hotel_id)})
    except Exception:
        ho = None
    if not ho:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    # Fetch rooms for hotel
    rooms = list(db.rooms.find({'hotel_id': ObjectId(hotel_id)}))
    room_ids = [str(r['_id']) for r in rooms]
    # Build date headers
    dates = [d.strftime('%Y-%m-%d') for d in _date_iter(s, e)]
    # Map rid -> set of booked dates
    booked_by_room = {rid: set() for rid in room_ids}
    q = {
        'hotel_id': hotel_id,
        'room_id': {'$in': room_ids},
        'status': 'confirmed',
        'check_in': {'$lt': end},
        'check_out': {'$gt': start},
    }
    for b in db.bookings.find(q, {'room_id': 1, 'check_in': 1, 'check_out': 1}):
        rid = b.get('room_id')
        bci = _parse_date(b.get('check_in') or '')
        bco = _parse_date(b.get('check_out') or '')
        if not rid or not bci or not bco or bco <= bci:
            continue
        for d in _date_iter(max(s, bci), min(e, bco)):
            booked_by_room[str(rid)].add(d.strftime('%Y-%m-%d'))
    # Build grid rows
    rows = []
    for r in rooms:
        rid = str(r['_id'])
        rn = r.get('room_number')
        rtype = r.get('type')
        row = {
            'room_id': rid,
            'room_number': rn,
            'type': rtype,
            'cells': [ (d in booked_by_room.get(rid, set())) for d in dates ]
        }
        rows.append(row)
    return jsonify({'ok': True, 'hotel_id': hotel_id, 'start': start, 'end': end, 'dates': dates, 'rows': rows})

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

@app.delete('/api/admin/bookings/<booking_id>')
def admin_delete_booking(booking_id):
    """Admin-only hard delete of a booking document."""
    a = actor()
    if a.get('role') != 'admin':
        return jsonify({'ok': False, 'error': 'Admin required'}), 403
    from bson import ObjectId
    try:
        oid = ObjectId(booking_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid booking id'}), 400
    res = db.bookings.delete_one({'_id': oid})
    if res.deleted_count == 0:
        return jsonify({'ok': False, 'error': 'Booking not found'}), 404
    return jsonify({'ok': True, 'deleted': True, 'booking_id': booking_id})

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
