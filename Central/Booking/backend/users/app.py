from flask import Flask, jsonify, request
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Mongo
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

def role_rank(role):
    return ROLE_HIERARCHY.get(role or 'guest', 0)

def can_act_on(actor, target, action, new_role=None):
    a_role = (actor or {}).get('role') or 'guest'
    t_role = (target or {}).get('role') or 'guest'
    if a_role not in ROLE_HIERARCHY:
        return False, 'invalid_actor_role'
    if action == 'delete' and actor.get('username') == target.get('username'):
        return False, 'cannot_delete_self'
    if a_role == 'manager' and t_role == 'admin':
        return False, 'manager_cannot_modify_admin'
    if role_rank(a_role) < role_rank(t_role):
        return False, 'insufficient_rank'
    if action == 'change_role':
        if new_role not in ROLE_HIERARCHY:
            return False, 'invalid_new_role'
        if a_role == 'manager' and new_role == 'admin':
            return False, 'manager_cannot_assign_admin'
        if t_role == 'admin' and new_role != 'admin':
            if db.users.count_documents({'role': 'admin', 'username': {'$ne': target.get('username')}}) == 0:
                return False, 'last_admin_protected'
    if action in ('delete','disable') and t_role == 'admin':
        if db.users.count_documents({'role': 'admin', 'username': {'$ne': target.get('username')}}) == 0:
            return False, 'last_admin_protected'
    return True, 'ok'

# ------------- Auth endpoints -------------
@app.post('/api/auth/login')
def auth_login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'ok': False, 'error': 'Username and password required'}), 400
    user = db.users.find_one({'username': username})
    if not user or user.get('active') is False:
        return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401
    stored = user.get('password') or ''
    if stored.startswith('pbkdf2:') or stored.startswith('scrypt:'):
        valid = check_password_hash(stored, password)
    else:
        valid = (stored == password)
    if not valid:
        return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401
    public_user = {
        'username': user['username'],
        'display_name': user.get('display_name', user['username']),
        'role': user.get('role', 'guest')
    }
    return jsonify({'ok': True, 'user': public_user})

@app.post('/api/auth/signup')
def auth_signup():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    display_name = (data.get('display_name') or username).strip() or username
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400
    if len(password) < 6:
        return jsonify({'ok': False, 'error': 'password too short'}), 400
    if db.users.find_one({'username': username}):
        return jsonify({'ok': False, 'error': 'username exists'}), 409
    hashed = generate_password_hash(password)
    doc = {
        'username': username,
        'password': hashed,
        'display_name': display_name,
        'role': 'guest',
        'active': True
    }
    db.users.insert_one(doc)
    public_user = {
        'username': username,
        'display_name': display_name,
        'role': 'guest'
    }
    return jsonify({'ok': True, 'user': public_user}), 201

@app.get('/api/users')
def list_users():
    a = actor()
    role = a.get('role')
    if role not in ('admin','manager'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    if role == 'admin':
        query = {}
    else:
        query = {'role': {'$in': ['manager','guest']}}
    docs = []
    for u in db.users.find(query, {'_id':0, 'password':0}):
        docs.append(u)
    return jsonify({'ok': True, 'users': docs})

@app.post('/api/users/create')
@app.post('/api/users')
def create_user():
    a = actor()
    if a.get('role') not in ('admin','manager'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    role_raw = (data.get('role') or 'guest').strip().lower()
    display_name = (data.get('display_name') or username).strip() or username
    if not username or not password:
        return jsonify({'ok': False, 'error': 'Missing fields: username, password'}), 400
    if role_raw not in ('admin','manager','guest'):
        return jsonify({'ok': False, 'error': 'Invalid role'}), 400
    if a.get('role') == 'manager' and role_raw == 'admin':
        return jsonify({'ok': False, 'error': 'Insufficient privileges for role'}), 403
    if db.users.find_one({'username': username}):
        return jsonify({'ok': False, 'error': 'Username exists'}), 409
    hashed = generate_password_hash(password)
    record = {'username': username, 'password': hashed, 'display_name': display_name, 'role': role_raw, 'active': True}
    db.users.insert_one(record)
    return jsonify({'ok': True, 'message': 'User created', 'user': {'username': username, 'display_name': display_name, 'role': role_raw, 'active': True}}), 201

@app.patch('/api/users/<username>')
def update_user(username):
    a = actor()
    if a.get('role') not in ('admin','manager'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    target = db.users.find_one({'username': username})
    if not target:
        return jsonify({'ok': False, 'error': 'User not found'}), 404
    data = request.get_json(silent=True) or {}
    updates = {}
    changed = []
    if 'display_name' in data:
        dn = (data.get('display_name') or '').strip()
        if dn and dn != target.get('display_name'):
            allowed, reason = can_act_on(a, target, 'edit')
            if not allowed:
                return jsonify({'ok': False, 'error': reason}), 403
            updates['display_name'] = dn
            changed.append('display_name')
    if 'active' in data:
        desired_active = bool(data.get('active'))
        if desired_active != (target.get('active', True)):
            action = 'disable' if not desired_active else 'edit'
            allowed, reason = can_act_on(a, target, action)
            if not allowed:
                return jsonify({'ok': False, 'error': reason}), 403
            updates['active'] = desired_active
            changed.append('active')
    if 'role' in data:
        new_role = (data.get('role') or '').strip().lower()
        if new_role and new_role != target.get('role'):
            allowed, reason = can_act_on(a, target, 'change_role', new_role=new_role)
            if not allowed:
                return jsonify({'ok': False, 'error': reason}), 403
            updates['role'] = new_role
            changed.append('role')
    if not updates:
        return jsonify({'ok': True, 'message': 'No changes'})
    db.users.update_one({'_id': target['_id']}, {'$set': updates})
    return jsonify({'ok': True, 'changed': changed})

@app.delete('/api/users/<username>')
def delete_user(username):
    a = actor()
    if a.get('role') not in ('admin','manager'):
        return jsonify({'ok': False, 'error': 'Auth required'}), 401
    target = db.users.find_one({'username': username})
    if not target:
        return jsonify({'ok': False, 'error': 'User not found'}), 404
    allowed, reason = can_act_on(a, target, 'delete')
    if not allowed:
        return jsonify({'ok': False, 'error': reason}), 403
    db.users.delete_one({'_id': target['_id']})
    return jsonify({'ok': True, 'deleted': username})

@app.post('/api/users/<username>/password-change')
def password_change(username):
    a = actor()
    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password') or ''
    current_password = data.get('current_password') or ''
    if len(new_password) < 6:
        return jsonify({'ok': False, 'error': 'Password too short'}), 400
    target = db.users.find_one({'username': username})
    if not target:
        return jsonify({'ok': False, 'error': 'User not found'}), 404
    if a.get('username') == username:
        stored = target.get('password') or ''
        if stored.startswith('pbkdf2:') or stored.startswith('scrypt:'):
            valid = check_password_hash(stored, current_password)
        else:
            valid = (stored == current_password)
        if not valid:
            return jsonify({'ok': False, 'error': 'Current password incorrect'}), 403
    else:
        allowed, reason = can_act_on(a, target, 'change_password')
        if not allowed:
            return jsonify({'ok': False, 'error': reason}), 403
    hashed = generate_password_hash(new_password)
    db.users.update_one({'_id': target['_id']}, {'$set': {'password': hashed}})
    return jsonify({'ok': True, 'message': 'Password updated'})

@app.get('/health')
def health():
    try:
        client.admin.command('ping')
        return {"ok": True, "mongo": "up"}
    except Exception as e:
        return {"ok": False, "mongo": "error", "error": str(e)}, 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5002'))
    app.run(host='0.0.0.0', port=port, debug=True)
