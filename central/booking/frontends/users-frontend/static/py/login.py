from js import document, fetch, console
import json, asyncio, datetime

try:
    from pyodide.ffi import create_proxy
except Exception:
    # older Pyodide fallback
    from pyodide import create_proxy

API_LOGIN = '/login?ajax=1'

# Debug flag: set to True to emit additional console information
DEBUG_ATTACH = True

status_el = document.getElementById('status')
btn = document.getElementById('submit-btn')
label_span = btn.querySelector('.btn-label') if btn else None


def set_status(message: str, kind: str):
    if not status_el:
        return
    status_el.className = 'status show ' + kind
    status_el.innerHTML = message


def clear_status():
    if not status_el:
        return
    status_el.className = 'status'
    status_el.innerHTML = ''


async def handle_submit(evt):
    evt.preventDefault()
    clear_status()
    
    form = document.getElementById('login-form')
    if not form:
        set_status('Form not found', 'error')
        return
    
    username = form.username.value.strip()
    password = form.password.value
    
    if len(username) < 3:
        set_status('Username must be at least 3 characters', 'error')
        return
    if len(password) < 6:
        set_status('Password must be at least 6 characters', 'error')
        return
    
    # Show loading state
    if btn:
        btn.disabled = True
        if label_span:
            label_span.innerHTML = 'Signing in...'
    
    try:
        payload = {'username': username, 'password': password}
        resp = await fetch(API_LOGIN, {
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            'body': json.dumps(payload),
            'redirect': 'manual', 
            'credentials': 'same-origin' 
        })
        
        if resp.status == 302:
            from js import window
            window.location.href = '/'
            return
        
        if resp.status != 200:
            set_status(f'Server error: {resp.status}', 'error')
            return
        
        if resp.status == 401:
            set_status('Invalid username or password', 'error')
            return
        
        ctype = resp.headers.get('Content-Type') if hasattr(resp, 'headers') else ''
        if 'application/json' not in ctype.lower():
            try:
                preview = await resp.text()
                preview_snip = (preview[:160] + '…') if len(preview) > 160 else preview
            except Exception as _e:
                preview_snip = f'<unreadable response: {_e}>'
            set_status(f'Unexpected non-JSON response (status {resp.status}). Preview: {preview_snip}', 'error')
            return
        data = await resp.json()
        result = data.to_py()
        
        if result.get('ok'):
            set_status('Login successful! Redirecting...', 'success')
            from js import window
            await asyncio.sleep(0.5)
            window.location.href = '/'
        else:
            set_status(result.get('error', 'Login failed'), 'error')
            
    except Exception as e:
        set_status(f'Error: {str(e)}', 'error')
    finally:
        if btn:
            btn.disabled = False
            if label_span:
                label_span.innerHTML = 'Sign In'

def attach():
    form = document.getElementById('login-form')
    if not form or getattr(form, "_py_handler", False):
        return
    
    form.addEventListener('submit', create_proxy(handle_submit))
    form._py_handler = True
    console.log("Login handler attached")

ready_state = document.readyState
if DEBUG_ATTACH:
    console.log(f"login.py loaded. document.readyState={ready_state}")

if ready_state == "loading":
    # Will run later
    if DEBUG_ATTACH:
        console.log("Adding DOMContentLoaded listener for login form attach")
    def _on_dom_loaded(e):
        if DEBUG_ATTACH:
            console.log("DOMContentLoaded fired -> attaching login handler")
        attach()
    document.addEventListener('DOMContentLoaded', create_proxy(_on_dom_loaded))
else:
    if DEBUG_ATTACH:
        console.log("Document already interactive/complete -> attaching now")
    attach()

# Fallback safety: if after a short delay the handler still not attached, log a warning
async def _post_check():
    await asyncio.sleep(0.25)
    form = document.getElementById('login-form')
    if form and not getattr(form, "_py_handler", False):
        console.warn("Login handler not attached after delay. Native form submit may cause GET /login?query. Check form id and script load order.")
try:
    asyncio.ensure_future(_post_check())
except Exception:
    pass

# Set year in footer
try:
    document.getElementById('year').innerHTML = str(datetime.datetime.now().year)
except Exception:
    pass
