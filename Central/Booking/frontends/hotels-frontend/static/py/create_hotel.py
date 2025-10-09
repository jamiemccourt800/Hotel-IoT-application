from js import document, console, window, fetch
import json

API_CREATE = '/api/hotels/create'

form = document.getElementById('create-hotel-form')
status_el = document.getElementById('status')
btn = document.getElementById('submit-btn')
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
    # Additional managers (comma separated)
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


if form:
    # PyScript/pyodide events: addEventListener works
    form.addEventListener('submit', submit_handler)
    console.debug('[create-hotel] submit listener attached (PyScript)')
else:
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
