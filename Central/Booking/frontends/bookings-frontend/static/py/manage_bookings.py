from js import document, fetch, window
import asyncio, json
from pyodide.ffi import create_proxy, to_js

status_el = document.getElementById('mb-status')
list_el = document.getElementById('mb-list')
sel_status = document.getElementById('filter-status')
input_hotel = document.getElementById('filter-hotel')
input_user = document.getElementById('filter-user')
btn_refresh = document.getElementById('btn-refresh')

API_LIST = '/api/admin/bookings'
API_STATUS = '/api/admin/bookings'


def set_status(msg, kind='error'):
    if status_el:
        status_el.className = f'status show {kind}'
        status_el.textContent = msg

def clear_status():
    if status_el:
        status_el.className = 'status'
        status_el.textContent = ''

async def load_bookings():
    clear_status()
    try:
        params = []
        st = sel_status.value if sel_status else ''
        if st:
            params.append(('status', st))
        hid = input_hotel.value if input_hotel else ''
        if hid:
            params.append(('hotel_id', hid))
        user = input_user.value if input_user else ''
        if user:
            params.append(('user', user))
        qs = '?' + '&'.join([f"{k}={v}" for k,v in params]) if params else ''
        r = await fetch(API_LIST + qs)
        if not r.ok:
            set_status(f'Failed to load bookings ({r.status})','error')
            return
        j = await r.json()
        py = j.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Load failed'),'error')
            return
        bookings = py.get('bookings') or []
        list_el.innerHTML = ''
        for b in bookings:
            list_el.appendChild(render_booking(b))
        set_status(f'Loaded {len(bookings)} booking(s)','success')
    except Exception as e:
        set_status(f'Error: {e}','error')

async def update_status(evt, booking_id, new_status, row):
    evt.preventDefault()
    try:
        btn = evt.currentTarget
        if btn:
            btn.disabled = True
        # Use to_js to ensure options are honored by fetch (method, headers, body)
        r = await fetch(
            f"{API_STATUS}/{booking_id}/status",
            to_js({
                'method': 'PATCH',
                'headers': { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                'body': json.dumps({ 'status': new_status })
            })
        )
        if not r.ok:
            set_status(f'Update failed ({r.status})','error')
            if btn:
                btn.disabled = False
            return
        j = await r.json()
        py = j.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Update failed'),'error')
            if btn:
                btn.disabled = False
            return
        # refresh row
        b = py.get('booking', {})
        new_row = render_booking(b)
        row.replaceWith(new_row)
        set_status('Status updated','success')
    except Exception as e:
        set_status(f'Error: {e}','error')
        try:
            if btn:
                btn.disabled = False
        except Exception:
            pass


def render_booking(b):
    row = document.createElement('div')
    row.className = 'booking-item'
    st = b.get('status')
    row.innerHTML = f'''
      <div class="bk-head">
        <div class="bk-hotel">
          <a href="/hotel/{b.get('hotel_id','')}" class="bk-hotel-name">{b.get('hotel_name','Hotel')}</a>
          <div class="bk-dates">{b.get('check_in','')} → {b.get('check_out','')} <span class="nights">({b.get('nights','?')} nights)</span></div>
        </div>
        <div class="bk-meta">
          <span class="bk-status {st}">{st.capitalize() if st else ''}</span>
          <span class="bk-total">${b.get('total_cost')}</span>
        </div>
      </div>
      <div class="bk-foot">
        <div class="bk-guests">Guests: {b.get('guests')}</div>
        <div class="bk-actions">''' + (
            '<span class="bk-cancelled-note">—</span>' if st in ('cancelled','denied') else
            f'<button type="button" class="mb-approve" data-id="{b.get("_id","")}">Approve</button>' +
            f'<button type="button" class="mb-deny" data-id="{b.get("_id","")}">Deny</button>'
        ) + '''</div>
      </div>
    '''
    if st not in ('cancelled','denied'):
        approve = row.querySelector('.mb-approve')
        deny = row.querySelector('.mb-deny')
        if approve:
            approve.addEventListener('click', create_proxy(lambda evt, bid=b.get('_id'), r=row: asyncio.ensure_future(update_status(evt, bid, 'confirmed', r))))
        if deny:
            deny.addEventListener('click', create_proxy(lambda evt, bid=b.get('_id'), r=row: asyncio.ensure_future(update_status(evt, bid, 'denied', r))))
    return row


if btn_refresh:
    btn_refresh.addEventListener('click', create_proxy(lambda evt: asyncio.ensure_future(load_bookings())))

asyncio.ensure_future(load_bookings())

try:
    from datetime import datetime
    document.getElementById('year').textContent = str(datetime.now().year)
    document.getElementById('p-year').textContent = str(datetime.now().year)
except Exception:
    pass
