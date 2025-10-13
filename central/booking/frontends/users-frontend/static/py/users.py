from js import document, fetch, prompt, window, console
import asyncio, json, datetime
from pyodide.ffi import create_proxy, to_js

API_USERS = '/api/users'
API_USERS_CREATE = '/api/users/create'

form = document.getElementById('user-form')
status_el = document.getElementById('user-status')
table_body = document.getElementById('users-tbody')
btn = document.getElementById('submit-btn')
role_select = document.getElementById('role')
_py_proxies = []  # prevent GC of event handlers
label_span = None
if btn:
    label_span = btn.querySelector('.btn-label')


def set_status(msg: str, kind: str = 'error'):
    if not status_el: return
    status_el.className = f'status-bar show {kind}'
    status_el.textContent = msg

def clear_status():
    if not status_el: return
    status_el.className = 'status-bar'
    status_el.textContent = ''

def serialize():
    if not form:
        return {}
    return {
        'username': form.username.value.strip(),
        'display_name': form.display.value.strip(),
        'password': form.password.value.strip(),
        'role': form.role.value.strip(),
    }

async def fetch_users():
    if not table_body:
        return
    try:
        resp = await fetch(API_USERS)
        if not getattr(resp, 'ok', False):
            return
        data = await resp.json()
        py = data.to_py()
        users = py.get('users', [])
        table_body.innerHTML = ''
        frag = document.createDocumentFragment()
        for u in users:
            tr = document.createElement('tr')
            username = u.get('username','')
            display_name = u.get('display_name','')
            role = u.get('role','')
            active = u.get('active', True)
            active_badge = 'Yes' if active else '<span style="color:#f87171;">No</span>'
            tr.innerHTML = (
              f'<td style="padding:.5rem .6rem; font-weight:600;">{username}</td>'
              f'<td style="padding:.5rem .6rem;">{display_name}</td>'
              f'<td style="padding:.5rem .6rem; text-transform:capitalize;">{role}</td>'
              f'<td style="padding:.5rem .6rem;">{active_badge}</td>'
              f'<td style="padding:.4rem .5rem; display:flex; gap:.35rem; flex-wrap:wrap;">'
                            f'<button type="button" class="u-btn" data-act="edit" data-user="{username}">Edit</button>'
                            f'<button type="button" class="u-btn" data-act="pw" data-user="{username}">Password</button>'
                            f'<button type="button" class="u-btn" data-act="tog" data-user="{username}">{"Disable" if active else "Enable"}</button>'
                            f'<button type="button" class="u-btn danger" data-act="del" data-user="{username}">Delete</button>'
              '</td>'
            )
            frag.appendChild(tr)
        table_body.appendChild(frag)
        bind_action_buttons()
    except Exception as e:
        set_status('Failed to load users: ' + str(e), 'error')

def bind_action_buttons():
    if not table_body: return
    buttons = table_body.querySelectorAll('button.u-btn')
    for b in buttons:
        if not getattr(b, '_bound', False):
            # Prevent default to avoid any accidental form submission or navigation
            def _on_click(ev, _btn=b):
                try:
                    if hasattr(ev, 'preventDefault'):
                        ev.preventDefault()
                    if hasattr(ev, 'stopPropagation'):
                        ev.stopPropagation()
                except Exception:
                    pass
                asyncio.ensure_future(handle_action(_btn))
            b.addEventListener('click', create_proxy(_on_click))
            b._bound = True

async def handle_action(btn):
    """Handle row action buttons (edit, password change, toggle active, delete)."""
    try:
        act = btn.getAttribute('data-act') or ''
        username = btn.getAttribute('data-user') or ''
        if not username:
            return
        if act == 'del':
            confirm_txt = prompt(f"Delete user '{username}'? Type DELETE to confirm")
            if confirm_txt != 'DELETE':
                return
            await do_delete(username)
            return
        if act == 'tog':
            # Toggle active flag
            row = btn.closest('tr')
            if not row:
                return
            active_cell = row.children[3]
            currently_active = 'No' not in active_cell.innerHTML
            await do_update(username, {'active': not currently_active})
            return
        if act == 'edit':
            row = btn.closest('tr')
            if not row:
                return
            cur_display = row.children[1].textContent
            new_display = prompt('New display name (leave blank to keep):', cur_display) or cur_display
            cur_role = row.children[2].textContent.lower()
            new_role = prompt(f"Role for {username} (admin/manager/guest) or blank to keep:", cur_role) or cur_role
            payload = {}
            if new_display != cur_display:
                payload['display_name'] = new_display
            if new_role != cur_role:
                payload['role'] = new_role
            if payload:
                await do_update(username, payload)
            return
        if act == 'pw':
            new_pw = prompt(f"Enter new password for {username} (min 6 chars):")
            if not new_pw:
                return
            if len(new_pw) < 6:
                set_status('Password too short', 'error')
                return
            await do_password(username, new_pw)
            return
    except Exception as e:
        set_status('Action error: ' + str(e), 'error')

async def submit_handler(evt):
    evt.preventDefault()
    console.debug('[create-user] submit intercepted (PyScript)')
    clear_status()
    payload = serialize()
    console.debug('[create-user] payload', payload)

    if btn:
        btn.disabled = True
        btn.classList.add('loading')
        if label_span:
            label_span.textContent = 'Creating...'

    try:
        console.debug('[create-user] POST', API_USERS_CREATE)
        resp = await fetch(API_USERS_CREATE, to_js({
            'method': 'POST',
            'headers': { 'Content-Type': 'application/json', 'Accept':'application/json' },
            'body': json.dumps(payload)
        }))
        status = resp.status
        text = await resp.text()
        console.debug('[create-user] response status', status)
        console.debug('[create-user] raw response', text)
        try:
            data = json.loads(text)
        except Exception as e:
            console.debug(f'[create-user] JSON parse error: {e}')
            set_status('Bad response', 'error')
            return
        if ((200 <= status < 300) and data.get('ok')) or data.get('user'):
            set_status(data.get('message','User created'), 'success')
            # Clear form fields after success (except role keep same for convenience)
            try:
                form.username.value = ''
                form.password.value = ''
                form.display.value = ''
            except Exception:
                pass
            # Refresh list
            await fetch_users()
        else:
            set_status(data.get('error', f'Create failed (status {resp.status})'), 'error')
    except Exception as e:
        console.debug(f'[create-user] Network error: {e}')
        set_status('Network error: ' + str(e), 'error')
    finally:
        if btn:
            btn.disabled = False
            btn.classList.remove('loading')
            if label_span:
                label_span.textContent = 'Create'

    # (Removed mis-placed action handling block; row action buttons handled separately by handle_action())

async def do_update(username, payload):
    try:
        resp = await fetch(f"{API_USERS}/{username}", to_js({
            'method': 'PATCH',
            'headers': {'Content-Type':'application/json','Accept':'application/json'},
            'body': json.dumps(payload)
        }))
        res_text = await resp.text()
        try:
            data = json.loads(res_text)
        except Exception:
            set_status('Bad response', 'error')
            return
        if getattr(resp, 'ok', False) and data.get('ok'):
            set_status('Updated', 'success')
            await fetch_users()
        else:
            set_status(data.get('error','Update failed'), 'error')
    except Exception as e:
        set_status('Network error: ' + str(e), 'error')

async def do_delete(username):
    try:
        resp = await fetch(f"{API_USERS}/{username}", to_js({'method': 'DELETE', 'headers': {'Accept':'application/json'}}))
        # If some layer forced a GET, retry with method override for resilience
        try:
            status = resp.status
        except Exception:
            status = 0
        if status == 405:
            resp = await fetch(f"{API_USERS}/{username}?_method=DELETE", to_js({'method': 'GET', 'headers': {'Accept':'application/json'}}))
        text = await resp.text()
        try:
            data = json.loads(text)
        except Exception:
            set_status('Bad response', 'error')
            return
        if getattr(resp, 'ok', False) and data.get('ok'):
            set_status('Deleted', 'success')
            await fetch_users()
        else:
            set_status(data.get('error','Delete failed'), 'error')
    except Exception as e:
        set_status('Network error: ' + str(e), 'error')

async def do_password(username, new_pw):
    try:
        resp = await fetch(f"{API_USERS}/{username}/password-change", to_js({
            'method': 'POST',
            'headers': {'Content-Type':'application/json','Accept':'application/json'},
            'body': json.dumps({'new_password': new_pw})
        }))
        text = await resp.text()
        try:
            data = json.loads(text)
        except Exception:
            set_status('Bad response', 'error')
            return
        if getattr(resp, 'ok', False) and data.get('ok'):
            set_status('Password updated', 'success')
        else:
            set_status(data.get('error','Password change failed'), 'error')
    except Exception as e:
        set_status('Network error: ' + str(e), 'error')

    # (Removed legacy form_submit using old element IDs)

if form:
    submit_proxy = create_proxy(lambda e: asyncio.ensure_future(submit_handler(e)))
    _py_proxies.append(submit_proxy)
    console.debug('[users.py] Binding unified submit handler')
    form.addEventListener('submit', submit_proxy)
    # Optional extra click binding (not strictly needed since button type=submit)
    if btn and not getattr(btn, '_bound', False):
        click_proxy = create_proxy(lambda e: asyncio.ensure_future(submit_handler(e)))
        _py_proxies.append(click_proxy)
        btn.addEventListener('click', click_proxy)
        btn._bound = True
    def _key_handler(ev):
        try:
            if ev.altKey and ev.shiftKey and ev.key.lower() == 'u':
                console.debug('[users.py] Alt+Shift+U: injecting test user')
                import time as _t
                form.username.value = 'test_' + str(int(_t.time()))[-5:]
                form.password.value = 'TestPass123!'
                asyncio.ensure_future(submit_handler(ev))
        except Exception as e:
            console.warn('[users.py] key handler error', e)
    key_proxy = create_proxy(_key_handler)
    _py_proxies.append(key_proxy)
    window.addEventListener('keydown', key_proxy)
    asyncio.ensure_future(fetch_users())
    # Global submit capture logger
    def _global_submit(ev):
        print('[users.py] window submit event captured target=', ev.target.id if hasattr(ev,'target') else 'unknown')
    global_submit_proxy = create_proxy(_global_submit)
    _py_proxies.append(global_submit_proxy)
    window.addEventListener('submit', global_submit_proxy, True)
    # Inject plain JS fallback for extreme cases
    js_fallback = document.createElement('script')
    js_fallback.textContent = (
        "window._userFormFallback = function(){try{const f=document.getElementById('user-form');" \
        "if(!f)return;const u=f.username.value.trim();const p=f.password.value;const r=f.role.value;" \
        "fetch('/api/users/create',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'}," \
        "body:JSON.stringify({username:u,password:p,role:r,display_name:f.display.value})})" \
        ".then(r=>r.text().then(t=>console.log('[fallback] status',r.status,t))).catch(e=>console.log('[fallback] err',e));}catch(e){console.log('[fallback] top err',e);}}"
    )
    document.body.appendChild(js_fallback)
    console.debug('[users.py] JS fallback injected: call _userFormFallback() manually if needed')
else:
    print('[users.py] Form not found at script load')

# Footer years
try:
    document.getElementById('year').textContent = str(datetime.datetime.now().year)
except Exception:
    pass
