from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import time

app = Flask(__name__)

# ------- Minimal Mongo Configuration -------
# Uses the same env vars as the rest of the stack for consistency.
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


# ---------------- Rooms API (bare minimum) ----------------
# POST /api/rooms
# Purpose: Create a room assigned to an existing hotel.
# Required fields: hotel_id (Mongo ObjectId string), room_number (string or int)
# Optional: type (str), capacity (int >= 0), price_per_night (float >= 0)
@app.post('/api/rooms')
def create_room():
    data = request.get_json(silent=True) or {}

    hotel_id_raw = (data.get('hotel_id') or '').strip()
    room_number = data.get('room_number')

    if not hotel_id_raw or room_number in (None, ''):
        return jsonify({'ok': False, 'error': 'hotel_id and room_number are required'}), 400

    # Validate hotel_id and ensure hotel exists.
    try:
        from bson import ObjectId
        hotel_oid = ObjectId(hotel_id_raw)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid hotel_id'}), 400

    if not db.hotels.find_one({'_id': hotel_oid}, {'_id': 1}):
        return jsonify({'ok': False, 'error': 'Hotel not found'}), 404

    # Normalize and validate optional fields.
    doc = {
        'hotel_id': hotel_oid,
        'room_number': str(room_number),
        'created_at': int(time.time()),
    }

    room_type = data.get('type')
    if room_type:
        doc['type'] = str(room_type)

    if 'capacity' in data and data['capacity'] not in (None, ''):
        try:
            cap = int(data['capacity'])
            if cap < 0:
                raise ValueError('negative')
            doc['capacity'] = cap
        except Exception:
            return jsonify({'ok': False, 'error': 'capacity must be a non-negative integer'}), 400

    if 'price_per_night' in data and data['price_per_night'] not in (None, ''):
        try:
            price = float(data['price_per_night'])
            if price < 0:
                raise ValueError('negative')
            doc['price_per_night'] = price
        except Exception:
            return jsonify({'ok': False, 'error': 'price_per_night must be a non-negative number'}), 400

    # Simple uniqueness guard: one room_number per hotel.
    if db.rooms.find_one({'hotel_id': hotel_oid, 'room_number': doc['room_number']}):
        return jsonify({'ok': False, 'error': 'Room already exists for this hotel'}), 409

    try:
        result = db.rooms.insert_one(doc)
        return jsonify({'ok': True, 'room_id': str(result.inserted_id), 'hotel_id': hotel_id_raw}), 201
    except Exception:
        return jsonify({'ok': False, 'error': 'DB insert failed'}), 500


@app.get('/api/rooms')
def list_rooms():
    """List rooms. Optional filter by hotel_id."""
    hotel_id_raw = (request.args.get('hotel_id') or '').strip()
    q = {}
    if hotel_id_raw:
        try:
            from bson import ObjectId
            q['hotel_id'] = ObjectId(hotel_id_raw)
        except Exception:
            return jsonify({'ok': False, 'error': 'Invalid hotel_id'}), 400
    try:
        limit = int(request.args.get('limit', 500))
    except Exception:
        limit = 500
    limit = max(1, min(limit, 1000))
    rooms = []
    for r in db.rooms.find(q).limit(limit):
        r['_id'] = str(r['_id'])
        if 'hotel_id' in r:
            try:
                r['hotel_id'] = str(r['hotel_id'])
            except Exception:
                pass
        rooms.append(r)
    return jsonify({'ok': True, 'rooms': rooms})


@app.get('/api/rooms/<room_id>')
def get_room(room_id):
    from bson import ObjectId
    try:
        oid = ObjectId(room_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room id'}), 400
    r = db.rooms.find_one({'_id': oid})
    if not r:
        return jsonify({'ok': False, 'error': 'Room not found'}), 404
    r['_id'] = str(r['_id'])
    try:
        r['hotel_id'] = str(r['hotel_id'])
    except Exception:
        pass
    return jsonify({'ok': True, 'room': r})


@app.patch('/api/rooms/<room_id>')
def update_room(room_id):
    from bson import ObjectId
    try:
        oid = ObjectId(room_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'Invalid room id'}), 400
    data = request.get_json(silent=True) or {}
    allowed = {'room_number', 'type', 'capacity', 'price_per_night'}
    updates = {}
    for k in allowed:
        if k in data:
            v = data.get(k)
            if k == 'room_number' and v not in (None, ''):
                v = str(v)
            if k == 'capacity' and v not in (None, ''):
                try:
                    v = int(v)
                    if v < 0:
                        raise ValueError('negative')
                except Exception:
                    return jsonify({'ok': False, 'error': 'capacity must be a non-negative integer'}), 400
            if k == 'price_per_night' and v not in (None, ''):
                try:
                    v = float(v)
                    if v < 0:
                        raise ValueError('negative')
                except Exception:
                    return jsonify({'ok': False, 'error': 'price_per_night must be a non-negative number'}), 400
            updates[k] = v
    if not updates:
        return jsonify({'ok': True, 'message': 'No changes'}), 200
    # If room_number is changing, enforce uniqueness within hotel
    if 'room_number' in updates:
        try:
            cur = db.rooms.find_one({'_id': oid})
            if cur and db.rooms.find_one({'hotel_id': cur.get('hotel_id'), 'room_number': updates['room_number'], '_id': {'$ne': oid}}):
                return jsonify({'ok': False, 'error': 'Room number already exists for this hotel'}), 409
        except Exception:
            pass
    res = db.rooms.update_one({'_id': oid}, {'$set': updates})
    if res.matched_count == 0:
        return jsonify({'ok': False, 'error': 'Room not found'}), 404
    r = db.rooms.find_one({'_id': oid})
    r['_id'] = str(r['_id'])
    try:
        r['hotel_id'] = str(r['hotel_id'])
    except Exception:
        pass
    return jsonify({'ok': True, 'room': r})


@app.get('/health')
def health():
    try:
        client.admin.command('ping')
        return {"ok": True, "mongo": "up"}
    except PyMongoError as e:
        return {"ok": False, "mongo": "error", "error": str(e)}, 500


if __name__ == '__main__':
    # Retain existing default port to avoid breaking docker-compose wiring.
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port, debug=True)
