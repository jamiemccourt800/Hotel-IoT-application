from js import document, fetch, console
import json, asyncio
from pyodide.ffi import create_proxy

form = document.getElementById('edit-form')
status_el = document.getElementById('status')

API_BASE = '/api/hotels'

def set_status(msg, kind='error'):
    if status_el:
        status_el.className = f'status show {kind}'
        status_el.textContent = msg

def clear_status():
    if status_el:
        status_el.className = 'status'
        status_el.textContent = ''

async def load_detail(hotel_id):
    try:
        r = await fetch(f'{API_BASE}/{hotel_id}')
        if not r.ok:
            set_status(f'Failed to load hotel ({r.status})','error')
            return
        data = await r.json()
        py = data.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Load failed'),'error')
            return
        h = py.get('hotel') or {}
        # Populate fields
        document.getElementById('name').value = h.get('name','')
        document.getElementById('city').value = h.get('city','')
        document.getElementById('country').value = h.get('country','')
        document.getElementById('price').value = h.get('price_per_night',0)
        document.getElementById('image').value = h.get('image','')
        rc_el = document.getElementById('room_count')
        if rc_el:
            rc_val = h.get('room_count')
            # Show 0 instead of blank if explicitly stored
            if rc_val is None or rc_val == '':
                rc_el.value = ''
            else:
                rc_el.value = str(rc_val)
        hidden_el = document.getElementById('hidden')
        if hidden_el and h.get('hidden'):
            hidden_el.checked = True
    except Exception as e:
        set_status(f'Error: {e}','error')

async def submit(evt):
    evt.preventDefault()
    console.log('[edit_hotel] submit handler entered')
    clear_status()
    hotel_id = form.getAttribute('data-hotel-id')
    if not hotel_id:
        set_status('Missing hotel id','error')
        return
    # Gather form values
    rc_raw = document.getElementById('room_count').value
    # Normalize room_count: keep empty string if user cleared it (won't send update) else int
    include_room = True
    if rc_raw.strip() == '':
        include_room = False  # don't update room_count if left blank
    else:
        try:
            rc_converted = int(rc_raw)
        except Exception:
            set_status('Room count must be an integer','error')
            return
    payload = {
        'name': document.getElementById('name').value.strip(),
        'city': document.getElementById('city').value.strip(),
        'country': document.getElementById('country').value.strip(),
        'price_per_night': document.getElementById('price').value,
        'image': document.getElementById('image').value.strip(),
        'hidden': document.getElementById('hidden').checked
    }
    if include_room:
        payload['room_count'] = rc_converted
    console.log('[edit_hotel] submitting PATCH', payload)
    btn = document.getElementById('save-btn')
    try:
        if btn:
            btn.disabled = True
            btn.textContent = 'Saving...'
        r = await fetch(f'{API_BASE}/{hotel_id}', {
            'method':'PATCH',
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps(payload)
        })
        ctype = r.headers.get('Content-Type') or ''
        if not r.ok:
            if 'application/json' in ctype:
                data = await r.json()
                py = data.to_py()
                set_status(py.get('error','Update failed'), 'error')
            else:
                set_status(f'Update failed ({r.status})','error')
            return
        data = await r.json()
        py = data.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Update failed'),'error')
            console.warn('[edit_hotel] update response not ok', py)
            return
        updated_fields = py.get('updated') or []
        if not updated_fields:
            # Server responded ok but no changes (maybe identical values)
            set_status('No changes (values identical)','success')
        else:
            set_status('Saved: ' + ', '.join(updated_fields),'success')
        console.log('[edit_hotel] update success', updated_fields)
        # Optionally re-fetch to show updated values
        asyncio.ensure_future(load_detail(hotel_id))
    except Exception as e:
        set_status(f'Error: {e}','error')
        console.error('[edit_hotel] submit error', e)
    finally:
        if btn:
            btn.disabled = False
            btn.textContent = 'Save Changes'
    console.log('[edit_hotel] submit handler exit')

if form:
    hid = form.getAttribute('data-hotel-id')
    console.log('[edit_hotel] form found, hotel id:', hid)
    if hid:
        asyncio.ensure_future(load_detail(hid))
    # Submit listener
    # Keep proxy reference globally to avoid GC
    global _submit_proxy
    _submit_proxy = create_proxy(submit)
    form.addEventListener('submit', _submit_proxy)
    # Fallback: also bind explicit click on save button in case browser bypasses submit event
    btn = document.getElementById('save-btn')
    if btn:
        async def click_wrap(evt):
            console.log('[edit_hotel] save-btn click fallback triggered')
            await submit(evt)
        btn.addEventListener('click', create_proxy(click_wrap))
else:
    console.warn('[edit_hotel] form#edit-form not found')

try:
    document.getElementById('year').textContent = str(__import__('datetime').datetime.now().year)
    document.getElementById('p-year').textContent = str(__import__('datetime').datetime.now().year)
except Exception:
    pass
