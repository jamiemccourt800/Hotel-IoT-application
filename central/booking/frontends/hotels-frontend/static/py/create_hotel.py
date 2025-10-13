from js import document, console, window, fetch
from pyodide.ffi import create_proxy
import asyncio
import json

API_CREATE = '/api/hotels/create'
API_USERS = '/api/users'

form = document.getElementById('create-hotel-form')
status_el = document.getElementById('status')
btn = document.getElementById('submit-btn')
picker = document.getElementById('manager-picker')
add_btn = document.getElementById('add-manager-btn')
chips_el = document.getElementById('managers-chips')
label_span = None
if btn:
    label_span = btn.querySelector('.btn-label')

console.debug('[create-hotel] PyScript init (external)')

def set_status(message: str, kind: str):
    if not status_el:
        return
    status_el.className = f'status show {kind}'
    status_el.textContent = message
    console.debug('[create-hotel] status', kind, message)


def clear_status():
    if not status_el:
        return
    status_el.className = 'status'
    status_el.textContent = ''


def serialize():
    if not form:
        return {}
    payload = {
        'name': form.name.value.strip(),
        'city': form.city.value.strip(),
        'country': form.country.value.strip(),
        'price_per_night': form.price_per_night.value.strip(),
        'image': form.image.value.strip(),
    }
    # Optional room_count
    if hasattr(form, 'room_count') and form.room_count.value.strip() != '':
        payload['room_count'] = form.room_count.value.strip()
    # Additional managers from hidden input (comma separated)
    if hasattr(form, 'managers') and form.managers.value.strip():
        raw_mgrs = [m.strip() for m in form.managers.value.split(',') if m.strip()]
        if raw_mgrs:
            payload['managers'] = raw_mgrs
    return payload


async def submit_handler(evt):
    evt.preventDefault()
    console.debug('[create-hotel] submit intercepted (PyScript)')
    clear_status()
    payload = serialize()
    console.debug('[create-hotel] payload', payload)
    if any(v == '' for v in payload.values()):
        set_status('All fields are required.', 'error')
        return

    if btn:
        btn.disabled = True
        btn.classList.add('loading')
        if label_span:
            label_span.textContent = 'Saving...'

    try:
        console.debug('[create-hotel] POST', API_CREATE)
        # Use fetch from JS world
        resp = await fetch(API_CREATE, {
            'method': 'POST',
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps(payload)
        })
        status = resp.status
        text = await resp.text()
        console.debug('[create-hotel] response status', status)
        console.debug('[create-hotel] raw response', text)
        try:
            data = json.loads(text)
        except Exception:
            set_status('Unexpected response format', 'error')
            return
        if ((200 <= status < 300) and data.get('ok')) or data.get('hotel_id'):
            set_status(data.get('message', 'Hotel created! Redirecting...'), 'success')
            def _redir():
                window.location.href = '/'
            window.setTimeout(_redir, 1100)
        else:
            set_status(data.get('error', 'Failed to create hotel'), 'error')
    except Exception as e:
        set_status(f'Network or server error: {e}', 'error')
    finally:
        if btn:
            btn.disabled = False
            btn.classList.remove('loading')
            if label_span:
                label_span.textContent = 'Create Hotel'


    def _submit_wrapper(evt):
        # Ensure default form submit is prevented synchronously
        try:
            evt.preventDefault()
        except Exception:
            pass
        console.debug('[create-hotel] submit wrapper fired (PyScript)')
        asyncio.ensure_future(submit_handler(evt))


    if form:
        # Wrap handler with create_proxy to avoid borrowed proxy GC issues
        submit_proxy = create_proxy(_submit_wrapper)
        form.addEventListener('submit', submit_proxy)
        # Keep reference to prevent GC
        if not hasattr(window, '_py_proxies'):
            window._py_proxies = []
        window._py_proxies.append(submit_proxy)
        console.debug('[create-hotel] submit listener attached (PyScript)')
    if not form:
        console.error('[create-hotel] form element not found (PyScript)')

# Autofill from query params
try:
    params = window.URLSearchParams(window.location.search)
    for k in ['name','city','country','price_per_night','image','room_count']:
        if params.has(k) and form and getattr(form, k, None):
            getattr(form, k).value = params.get(k)
except Exception as e:
    console.debug('[create-hotel] autofill skipped', e)

# Footer year
year_el = document.getElementById('year')
if year_el:
    from datetime import datetime
    year_el.textContent = str(datetime.now().year)

# -------- Manager picker logic --------
selected_mgrs = set()

def _render_chips():
    if not chips_el:
        return
    # Clear chips
    chips_el.innerHTML = ''
    for uname in sorted(selected_mgrs):
        chip = document.createElement('span')
        chip.setAttribute('class', 'user-badge')
        chip.style.display = 'inline-flex'
        chip.style.alignItems = 'center'
        chip.style.gap = '.35rem'
        chip.textContent = uname
        # remove button
        rm = document.createElement('button')
        rm.textContent = '×'
        rm.setAttribute('aria-label', f'Remove {uname}')
        rm.style.background = 'transparent'
        rm.style.border = 'none'
        rm.style.color = 'var(--text-dim)'
        rm.style.cursor = 'pointer'
        # create_proxy for click handler and retain reference
        rm_proxy = create_proxy(lambda ev, u=uname: _remove_mgr(u))
        rm.addEventListener('click', rm_proxy)
        if not hasattr(window, '_py_proxies'):
            window._py_proxies = []
        window._py_proxies.append(rm_proxy)
        chip.appendChild(rm)
        chips_el.appendChild(chip)
    # sync hidden input
    hidden = document.getElementById('managers')
    if hidden is not None:
        hidden.value = ','.join(sorted(selected_mgrs))

def _remove_mgr(uname: str):
    if uname in selected_mgrs:
        selected_mgrs.remove(uname)
        _render_chips()

async def _load_users():
    if not picker:
        return
    try:
        resp = await fetch(API_USERS, { 'headers': { 'Accept': 'application/json' }})
        text = await resp.text()
        data = json.loads(text)
        options = []
        if data.get('ok') and isinstance(data.get('users'), list):
            for u in data['users']:
                role = (u.get('role') or '').lower()
                if role in ('admin','manager'):
                    options.append({ 'username': u.get('username'), 'display_name': u.get('display_name') or u.get('username') })
        # Populate select
        picker.innerHTML = ''
        # placeholder option
        ph = document.createElement('option')
        ph.value = ''
        ph.textContent = 'Select a manager to add'
        ph.disabled = True
        ph.selected = True
        picker.appendChild(ph)
        for opt in options:
            el = document.createElement('option')
            el.value = opt['username']
            el.textContent = f"{opt['display_name']} ({opt['username']})"
            picker.appendChild(el)
    except Exception as e:
        console.error('[create-hotel] failed to load users', e)
        if picker:
            picker.innerHTML = ''
            err = document.createElement('option')
            err.value = ''
            err.textContent = 'Failed to load users'
            err.disabled = True
            err.selected = True
            picker.appendChild(err)

def _add_selected_mgr(evt=None):
    if not picker:
        return
    uname = (picker.value or '').strip()
    if not uname:
        return
    if uname in selected_mgrs:
        return
    selected_mgrs.add(uname)
    _render_chips()
    # keep placeholder after add
    picker.value = ''

# Wire add button (with proxies)
if not hasattr(window, '_py_proxies'):
    window._py_proxies = []
if add_btn:
    add_proxy = create_proxy(_add_selected_mgr)
    add_btn.addEventListener('click', add_proxy)
    window._py_proxies.append(add_proxy)
if picker:
    change_proxy = create_proxy(_add_selected_mgr)
    picker.addEventListener('change', change_proxy)
    window._py_proxies.append(change_proxy)

# Kick off user load asynchronously and initial render
asyncio.ensure_future(_load_users())
_render_chips()
