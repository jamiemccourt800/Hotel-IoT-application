from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import time

app = Flask(__name__)

# ------- Mongo Configuration -------
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb") or "mongodb"
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "bookings")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")

if MONGO_USER and MONGO_PASS:
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}"
else:
    uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"

client = MongoClient(uri)
db = client[MONGO_DB]

ROLE_HIERARCHY = {'admin': 3, 'manager': 2, 'guest': 1}

def current_actor():
    username = (request.headers.get('X-User-Name') or '').strip()
    role = (request.headers.get('X-User-Role') or 'guest').strip().lower()
    if role not in ROLE_HIERARCHY:
        role = 'guest'
    return {'username': username or None, 'role': role}

def can_manage_hotel(actor, hotel_doc):
    if not actor:
        return False
    if actor.get('role') == 'admin':
        return True
    if actor.get('role') == 'manager':
        managers = hotel_doc.get('managers') or []
        return actor.get('username') in managers
    return False

# ---- Rooms count helpers ----
def _room_counts_for(hotel_ids):
    """Return a dict of {ObjectId: count} for provided hotel ObjectIds."""
    counts = {}
    if not hotel_ids:
        return counts
    try:
        pipeline = [
            {'$match': {'hotel_id': {'$in': hotel_ids}}},
            {'$group': {'_id': '$hotel_id', 'count': {'$sum': 1}}},
        ]
        for row in db.rooms.aggregate(pipeline):
            hid = row.get('_id')
            cnt = int(row.get('count') or 0)
            counts[hid] = cnt
    except Exception:
        # If rooms collection missing or any issue, fall back to empty
        pass
    return counts

def _room_count_for(hotel_oid):
    try:
        return int(db.rooms.count_documents({'hotel_id': hotel_oid}))
    except Exception:
        return int(0)

@app.get('/api/hotels')
def list_hotels():
    q = (request.args.get('q') or '').strip()
    city = (request.args.get('city') or '').strip()
    sort = (request.args.get('sort') or '').strip().lower()
    try:
        limit = int(request.args.get('limit', 250))
    except ValueError:
        limit = 250
    limit = max(1, min(limit, 500))

    mongo_query = {}
    if q and city:
        mongo_query = {'$and': [
            {'$or': [{'name': {'$regex': q, '$options': 'i'}}, {'city': {'$regex': q, '$options': 'i'}}]},
            {'city': city}
        ]}
    elif q:
        mongo_query = {'$or': [{'name': {'$regex': q, '$options': 'i'}}, {'city': {'$regex': q, '$options': 'i'}}]}
    elif city:
        mongo_query = {'city': city}

    sort_spec = None
    if sort == 'price_asc':
        sort_spec = [('price_per_night', 1)]
    elif sort == 'price_desc':
        sort_spec = [('price_per_night', -1)]
    elif sort == 'name_asc':
        sort_spec = [('name', 1)]
    elif sort == 'name_desc':
        sort_spec = [('name', -1)]

    managed_only = (request.args.get('managed') == '1')
    actor = current_actor()
    try:
        base_query = mongo_query.copy()
        if managed_only:
            if actor and actor.get('role') != 'admin':
                base_query['managers'] = {'$in': [actor.get('username')]}
        else:
            if not actor or actor.get('role') != 'admin':
                base_query = {'$and': [mongo_query, {'$or': [
                    {'hidden': {'$ne': True}},
                    {'managers': {'$in': [actor.get('username') if actor else None]}}
                ]}]}

        cursor = db.hotels.find(base_query)
        if sort_spec:
            cursor = cursor.sort(sort_spec)
        cursor = cursor.limit(limit)
        # materialize to list to compute room counts in bulk
        hotels = list(cursor)
        hotel_ids = [h.get('_id') for h in hotels if h.get('_id')]
        rc_map = _room_counts_for(hotel_ids)
        docs = []
        for hotel in hotels:
            shaped = {
                'hotel_id': str(hotel.get('_id')),
                'name': hotel.get('name', ''),
                'city': hotel.get('city', ''),
                'country': hotel.get('country', ''),
                'price_per_night': hotel.get('price_per_night', 0),
                'image': hotel.get('image', '')
            }
            if hotel.get('hidden') is True:
                shaped['hidden'] = True
            if can_manage_hotel(actor, hotel):
                shaped['managers'] = hotel.get('managers', [])
                shaped['created_by'] = hotel.get('created_by')
                shaped['created_at'] = hotel.get('created_at')
                shaped['room_count'] = int(rc_map.get(hotel.get('_id'), 0))
            docs.append(shaped)
        return jsonify({'ok': True, 'hotels': docs})
    except Exception:
        return jsonify({'ok': False, 'error': 'Database query failed'}), 500

@app.get('/api/hotels/cities')
def list_cities():
    try:
        cities = sorted(set([d.get('city') for d in db.hotels.find({}, {'city': 1, '_id': 0}) if d.get('city')]))
        return jsonify({'ok': True, 'cities': cities})
    except Exception:
        return jsonify({'ok': False, 'error': 'Query failed'}), 500

@app.post('/api/hotels/create')
def create_hotel():
    actor = current_actor()
    if actor.get('role') not in ('admin', 'manager'):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    raw_json = request.get_json(silent=True)
    data = raw_json if isinstance(raw_json, dict) else {}
    required = ["name", "city", "country", "price_per_night", "image"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"ok": False, "error": f"Missing fields: {', '.join(missing)}"}), 400
    try:
        try:
            data["price_per_night"] = float(data["price_per_night"])
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "price_per_night must be numeric"}), 400
        room_count = 0
        if data.get('room_count') not in (None, ''):
            try:
                room_count = int(data.get('room_count'))
                if room_count < 0:
                    raise ValueError('negative')
            except Exception:
                return jsonify({"ok": False, "error": "room_count must be a non-negative integer"}), 400
        data['room_count'] = room_count
        input_managers = []
        raw_mgrs = data.get('managers')
        if isinstance(raw_mgrs, list):
            input_managers = [str(x).strip() for x in raw_mgrs if str(x).strip()]
        creator = actor.get('username') or 'unknown'
        managers = list({creator, *input_managers})
        data['managers'] = managers
        data['created_by'] = creator
        data['created_at'] = int(time.time())
        hidden_raw = data.get('hidden')
        hidden = False
        if isinstance(hidden_raw, str):
            hidden = hidden_raw.lower() in ('1', 'true', 'yes', 'on')
        elif isinstance(hidden_raw, bool):
            hidden = hidden_raw
        data['hidden'] = hidden
        result = db.hotels.insert_one(data)
        hid = str(result.inserted_id)
        return jsonify({"ok": True, "message": "Hotel created", "hotel_id": hid, "managers": managers, "room_count": room_count}), 201
    except Exception:
        return jsonify({"ok": False, "error": "DB insert failed"}), 500

@app.patch('/api/hotels/<hotel_id>')
def update_hotel(hotel_id):
    from bson import ObjectId
    try:
        oid = ObjectId(hotel_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid hotel id'}), 400
    hotel = db.hotels.find_one({'_id': oid})
    if not hotel:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    actor = current_actor()
    if not can_manage_hotel(actor, hotel):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    data = request.get_json(silent=True) or {}
    editable_fields = {'name', 'city', 'country', 'price_per_night', 'image', 'room_count', 'hidden'}
    updates = {}
    for k in editable_fields:
        if k in data:
            v = data.get(k)
            if k == 'price_per_night':
                try:
                    v = float(v)
                except (ValueError, TypeError):
                    return jsonify({'ok': False, 'error': 'price_per_night must be numeric'}), 400
            if k == 'room_count':
                try:
                    v = int(v)
                    if v < 0:
                        raise ValueError('negative')
                except (ValueError, TypeError):
                    return jsonify({'ok': False, 'error': 'room_count must be a non-negative integer'}), 400
            if k == 'hidden':
                if isinstance(v, str):
                    v = v.lower() in ('1', 'true', 'yes', 'on')
                else:
                    v = bool(v)
            if v is not None and v != hotel.get(k):
                updates[k] = v
    if not updates:
        return jsonify({'ok': True, 'message': 'No changes'}), 200
    try:
        db.hotels.update_one({'_id': oid}, {'$set': updates})
        return jsonify({'ok': True, 'updated': list(updates.keys())})
    except Exception:
        return jsonify({'ok': False, 'error': 'Update failed'}), 500

@app.get('/api/hotels/<hotel_id>')
def hotel_detail(hotel_id):
    from bson import ObjectId
    try:
        oid = ObjectId(hotel_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid hotel id'}), 400
    hotel = db.hotels.find_one({'_id': oid})
    if not hotel:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    actor = current_actor()
    shaped = {
        'hotel_id': str(hotel.get('_id')),
        'name': hotel.get('name', ''),
        'city': hotel.get('city', ''),
        'country': hotel.get('country', ''),
        'price_per_night': hotel.get('price_per_night', 0),
        'image': hotel.get('image', ''),
        'created_at': hotel.get('created_at')
    }
    try:
        import datetime
        ts = hotel.get('created_at')
        if ts:
            shaped['created_at_iso'] = datetime.datetime.utcfromtimestamp(int(ts)).isoformat() + 'Z'
    except Exception:
        pass
    # Always compute room_count from rooms collection
    rc_dynamic = _room_count_for(oid)
    if can_manage_hotel(actor, hotel):
        shaped['managers'] = hotel.get('managers', [])
        shaped['created_by'] = hotel.get('created_by')
        shaped['room_count'] = rc_dynamic
    else:
        rc = rc_dynamic
        if isinstance(rc, int) and rc > 0:
            shaped['capacity_hint'] = 'Available'
    return jsonify({'ok': True, 'hotel': shaped})

@app.post('/api/hotels/<hotel_id>/managers')
def add_manager(hotel_id):
    from bson import ObjectId
    try:
        oid = ObjectId(hotel_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid hotel id'}), 400
    hotel = db.hotels.find_one({'_id': oid})
    if not hotel:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    actor = current_actor()
    if not can_manage_hotel(actor, hotel):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    if not username:
        return jsonify({'ok': False, 'error': 'username required'}), 400
    target = db.users.find_one({'username': username})
    if not target:
        return jsonify({'ok': False, 'error': 'User not found'}), 404
    if target.get('role') not in ('manager', 'admin'):
        return jsonify({'ok': False, 'error': 'User must have manager or admin role'}), 400
    managers = hotel.get('managers') or []
    if username in managers:
        return jsonify({'ok': True, 'message': 'Already a manager'})
    managers.append(username)
    try:
        db.hotels.update_one({'_id': oid}, {'$set': {'managers': managers}})
        return jsonify({'ok': True, 'managers': managers})
    except Exception:
        return jsonify({'ok': False, 'error': 'Update failed'}), 500

@app.delete('/api/hotels/<hotel_id>/managers')
def remove_manager(hotel_id):
    from bson import ObjectId
    try:
        oid = ObjectId(hotel_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid hotel id'}), 400
    hotel = db.hotels.find_one({'_id': oid})
    if not hotel:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    actor = current_actor()
    if not can_manage_hotel(actor, hotel):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    if not username:
        return jsonify({'ok': False, 'error': 'username required'}), 400
    managers = hotel.get('managers') or []
    if username not in managers:
        return jsonify({'ok': False, 'error': 'Not a manager'}), 404
    if len(managers) == 1:
        return jsonify({'ok': False, 'error': 'Cannot remove last manager'}), 400
    managers = [m for m in managers if m != username]
    try:
        db.hotels.update_one({'_id': oid}, {'$set': {'managers': managers}})
        return jsonify({'ok': True, 'managers': managers})
    except Exception:
        return jsonify({'ok': False, 'error': 'Update failed'}), 500

@app.patch('/api/hotels/<hotel_id>/visibility')
def toggle_visibility(hotel_id):
    from bson import ObjectId
    try:
        oid = ObjectId(hotel_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid hotel id'}), 400
    hotel = db.hotels.find_one({'_id': oid})
    if not hotel:
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404
    actor = current_actor()
    if not can_manage_hotel(actor, hotel):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    data = request.get_json(silent=True) or {}
    hidden_raw = data.get('hidden')
    if hidden_raw is None:
        new_hidden = not bool(hotel.get('hidden'))
    else:
        if isinstance(hidden_raw, str):
            new_hidden = hidden_raw.lower() in ('1', 'true', 'yes', 'on')
        else:
            new_hidden = bool(hidden_raw)
    try:
        db.hotels.update_one({'_id': oid}, {'$set': {'hidden': new_hidden}})
        return jsonify({'ok': True, 'hidden': new_hidden})
    except Exception:
        return jsonify({'ok': False, 'error': 'Update failed'}), 500

@app.get('/health')
def health():
    try:
        client.admin.command('ping')
        return {"ok": True, "mongo": "up"}
    except PyMongoError as e:
        return {"ok": False, "mongo": "error", "error": str(e)}, 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port, debug=True)
