from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os
import logging
import time
import uuid

app = Flask(__name__, template_folder='template', static_folder='static', static_url_path='')

# ------- Logging Configuration -------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_level = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(level=_level,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
app.logger.setLevel(_level)
app.logger.info(f"Logging initialized at level {_level}")

MONGO_HOST = os.getenv("MONGO_HOST", "mongodb") or "mongodb"
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB   = os.getenv("MONGO_DB", "bookings")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")

if MONGO_USER and MONGO_PASS:
    uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}"
    auth_mode = 'auth'
else:
    uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"
    auth_mode = 'no-auth'
client = MongoClient(uri)

try:
    client.admin.command('ping')
    app.logger.info(f"Mongo connected mode={auth_mode} host={MONGO_HOST} db={MONGO_DB}")
except Exception as e:
    app.logger.error(f"Mongo connection failed: {e}")

db = client[MONGO_DB]

# -------- Utility helpers (logging / sanitization) ---------
SENSITIVE_KEYS = {"password", "pass", "pwd", "secret", "token"}

def _sanitize(obj):
    if isinstance(obj, dict):
        return {k: ('***' if k.lower() in SENSITIVE_KEYS else _sanitize(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj

@app.before_request
def _log_request_start():
    request._start_time = time.time()
    req_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    request._req_id = req_id
    payload = None
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            payload = request.get_json(silent=True)
        except Exception:
            payload = None
    app.logger.info(
        {
            "event": "request_start",
            "id": req_id,
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "args": request.args.to_dict(flat=True),
            "payload": _sanitize(payload) if payload else None
        }
    )

@app.after_request
def _log_request_end(response):
    duration_ms = None
    if hasattr(request, '_start_time'):
        duration_ms = round((time.time() - request._start_time) * 1000, 2)
    req_id = getattr(request, '_req_id', '-')
    # Attach request id header for traceability
    response.headers['X-Request-ID'] = req_id
    try:
        app.logger.info({
            "event": "request_end",
            "id": req_id,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "path": request.path,
            "method": request.method
        })
    except Exception:
        pass
    return response

@app.route('/')
def hotels_page():
    return render_template('hotels.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/hotels')
def api_hotels():
    hotels_collection = db.hotels
    try:
        docs = []
        for hotel in hotels_collection.find({}, {"_id": 0}):
            docs.append({
                "name": hotel.get("name", ""),
                "city": hotel.get("city", ""),
                "country": hotel.get("country", ""),
                "price_per_night": hotel.get("price_per_night", 0),
                "image": hotel.get("image", "")
            })
        app.logger.debug({
            "event": "fetch_hotels_success",
            "count": len(docs)
        })
        return jsonify({"ok": True, "hotels": docs})
    except Exception as e:
        app.logger.exception("Failed to fetch hotels")
        return jsonify({"ok": False, "error": "Database auth or query failed"}), 500


#TODO: PROTECT THIS SOMEHOW
@app.route('/create-hotel')
def create_hotel_page():
    return render_template('create_hotel.html')

def check_credentials(username, password):
    """Check credentials against the users collection in MongoDB."""
    user = db.users.find_one({"username": username})
    if user and user.get("password") == password:
        return {
            "username": user["username"],
            "display_name": user.get("display_name", user["username"])
        }
    return None

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        app.logger.warning({
            "event": "login_missing_fields",
            "username_present": bool(username),
            "password_present": bool(password)
        })
        return jsonify({"ok": False, "error": "Username and password required"}), 400

    user = check_credentials(username, password)
    if user:
        app.logger.info({
            "event": "login_success",
            "username": username
        })
        return jsonify({
            "ok": True,
            "user": user
        })
    app.logger.warning({
        "event": "login_failed",
        "username": username
    })
    return jsonify({"ok": False, "error": "Invalid credentials"}), 401

@app.route('/api/create-hotel', methods=['POST'])
def create_hotel():
    raw_json = request.get_json(silent=True)
    data = raw_json if isinstance(raw_json, dict) else None
    source = 'json'
    if not data:
        if request.form:
            data = {k: v for k, v in request.form.items()}
            source = 'form'
        elif request.args:  # fallback (shouldn't normally hit because POST)
            data = {k: v for k, v in request.args.items()}
            source = 'query'
    if not data:
        data = {}
    app.logger.debug({
        "event": "create_hotel_input_parsed",
        "source": source,
        "keys": list(data.keys())
    })
    required = ["name", "city", "country", "price_per_night", "image"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        app.logger.warning({
            "event": "create_hotel_missing_fields",
            "missing": missing
        })
        return jsonify({"ok": False, "error": f"Missing fields: {', '.join(missing)}"}), 400
    try:
        # Normalize
        try:
            data["price_per_night"] = float(data["price_per_night"])
        except (ValueError, TypeError):
            app.logger.warning({
                "event": "create_hotel_invalid_price",
                "raw_value": data.get("price_per_night")
            })
            return jsonify({"ok": False, "error": "price_per_night must be numeric"}), 400
        result = db.hotels.insert_one(data)
        app.logger.info({
            "event": "create_hotel_success",
            "name": data.get("name"),
            "city": data.get("city"),
            "country": data.get("country"),
            "hotel_id": str(result.inserted_id)
        })
        return jsonify({"ok": True, "message": "Hotel created", "hotel_id": str(result.inserted_id)}), 201
    except Exception as e:
        app.logger.exception("create_hotel_failure")
        return jsonify({"ok": False, "error": "DB insert failed"}), 500


##TODO: PROTECT THIS SOMEHOW
@app.route('/setup', methods=['POST'])
def setup():
    """Setup route to create initial admin user."""
    data = request.get_json(silent=True) or {}
    username = data.get('username', 'admin').strip()
    password = data.get('password', 'password123')
    display_name = data.get('display_name', 'Administrator')

    if db.users.find_one({"username": username}):
        app.logger.info({
            "event": "setup_user_exists",
            "username": username
        })
        return jsonify({"ok": False, "error": "User already exists"}), 400

    db.users.insert_one({
        "username": username,
        "password": password,
        "display_name": display_name
    })
    app.logger.info({
        "event": "setup_user_created",
        "username": username
    })
    return jsonify({"ok": True, "message": "Admin user created"})

@app.route('/health')
def health():
    try:
        client.admin.command('ping')
        app.logger.debug({"event": "health_ok"})
        return {"ok": True, "mongo": "up"}
    except PyMongoError as e:
        app.logger.error({"event": "health_error", "error": str(e)})
        return {"ok": False, "mongo": "error", "error": str(e)}, 500

#TODO: HOTEL VIEW
#TODO: BOOKING
#TODO: ADMIN VIEW
#TODO: BOOKING VIEW
#TODO: EDIT HOTEL

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
