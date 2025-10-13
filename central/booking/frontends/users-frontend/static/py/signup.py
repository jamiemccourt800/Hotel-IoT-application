from js import document, fetch, window
import json, datetime

API_SIGNUP = '/signup?ajax=1'

form = document.getElementById('signup-form')
status_el = document.getElementById('status')
btn = document.getElementById('submit-btn')
label_span = btn.querySelector('.btn-label') if btn else None


def set_status(msg, kind='error'):
    if not status_el:
        return
    status_el.className = f'status show {kind}'
    status_el.textContent = msg


def clear_status():
    if not status_el:
        return
    status_el.className = 'status'
    status_el.textContent = ''


async def submit_handler(evt):
    evt.preventDefault()
    clear_status()
    if not form:
        set_status('Form not found', 'error')
        return
    username = form.username.value.strip()
    password = form.password.value
    display_name = form.display_name.value.strip()
    if not username or not password:
        set_status('Username and password required', 'error')
        return
    if len(password) < 6:
        set_status('Password too short', 'error')
        return
    payload = {'username': username, 'password': password}
    if display_name:
        payload['display_name'] = display_name
    if btn:
        btn.disabled = True
        if label_span:
            label_span.textContent = 'Creating...'
    try:
        resp = await fetch(API_SIGNUP, {
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            'body': json.dumps(payload),
            'credentials': 'same-origin'
        })
        status = resp.status
        try:
            data = await resp.json()
            py = data.to_py()
        except Exception:
            set_status('Unexpected response format', 'error')
            return
        if status == 201 and py.get('ok'):
            set_status('Account created! Redirecting...', 'success')
            def _redir():
                window.location.href = '/'
            window.setTimeout(_redir, 900)
        else:
            set_status(py.get('error','Signup failed'), 'error')
    except Exception as e:
        set_status(f'Error: {e}', 'error')
    finally:
        if btn:
            btn.disabled = False
            if label_span:
                label_span.textContent = 'Create Account'

# Attach
try:
    from pyodide.ffi import create_proxy
    if form:
        form.addEventListener('submit', create_proxy(submit_handler))
except Exception:
    pass

# Footer year
try:
    document.getElementById('year').textContent = str(datetime.datetime.now().year)
except Exception:
    pass
