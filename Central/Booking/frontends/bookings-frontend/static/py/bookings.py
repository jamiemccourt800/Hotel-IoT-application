from js import document, fetch, window
import asyncio, json
from pyodide.ffi import create_proxy

status_el = document.getElementById('bookings-status')
list_el = document.getElementById('bookings-list')
empty_el = document.getElementById('empty')
loading_el = document.getElementById('loading')

API_LIST = '/api/bookings'
API_CANCEL = '/api/bookings'

def set_status(msg, kind='error'):
    if status_el:
        status_el.className = f'status show {kind}'
        status_el.textContent = msg

def clear_status():
    if status_el:
        status_el.className = 'status'
        status_el.textContent = ''

def fmt_date(s):
    return s or ''

def escape_html(s):
    return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

async def load_bookings():
    clear_status()
    try:
        r = await fetch(API_LIST)
        if not r.ok:
            set_status(f'Failed to load bookings ({r.status})','error')
            return
        data = await r.json()
        py = data.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Load failed'),'error')
            return
        bookings = py.get('bookings') or []
        if loading_el:
            loading_el.remove()
        if not bookings:
            if empty_el:
                empty_el.hidden = False
            return
        if list_el:
            list_el.hidden = False
            list_el.innerHTML = ''
            for b in bookings:
                list_el.appendChild(render_booking(b))
    except Exception as e:
        set_status(f'Error: {e}','error')

async def cancel_booking(evt, booking_id, wrapper, btn_el=None):
    evt.preventDefault()
    if not window.confirm('Cancel this booking?'):
        return
    try:
        # Resolve the button element robustly
        btn = btn_el or getattr(evt, 'currentTarget', None) or getattr(evt, 'target', None)
        if btn is not None:
            btn.disabled = True
            btn.textContent = 'Cancelling…'
        r = await fetch(f"{API_CANCEL}/{booking_id}", { 'method': 'DELETE' })
        ctype = r.headers.get('Content-Type') or ''
        if not r.ok:
            msg = f'Cancel failed ({r.status})'
            if 'application/json' in ctype:
                try:
                    j = await r.json()
                    pj = j.to_py()
                    if pj.get('error'): msg = pj.get('error')
                except Exception:
                    pass
            set_status(msg,'error')
            if btn is not None:
                btn.disabled = False
                btn.textContent = 'Cancel'
            return
        if 'application/json' in ctype:
            j = await r.json()
            pj = j.to_py()
            if not pj.get('ok'):
                set_status(pj.get('error','Cancel failed'),'error')
                if btn is not None:
                    btn.disabled = False
                    btn.textContent = 'Cancel'
                return
        # update UI
        st = wrapper.querySelector('.bk-status')
        if st:
            st.textContent = 'Cancelled'
            st.classList.remove('confirmed')
            st.classList.add('cancelled')
        acts = wrapper.querySelector('.bk-actions')
        if acts:
            acts.innerHTML = '<span class="bk-cancelled-note">—</span>'
        set_status('Booking cancelled','success')
    except Exception as e:
        set_status(f'Error: {e}','error')
    finally:
        if btn is not None:
            try:
                btn.disabled = False
            except Exception:
                pass

def render_booking(b):
    wrap = document.createElement('div')
    wrap.className = 'booking-item'
    status = b.get('status')
    nights = b.get('nights')
    if nights is None:
        # Fallback compute
        try:
            from datetime import datetime
            ci = datetime.fromisoformat(b.get('check_in'))
            co = datetime.fromisoformat(b.get('check_out'))
            nights = max(0,(co-ci).days)
        except Exception:
            nights = 0
    total = b.get('total_cost')
    cancelled = b.get('status') == 'cancelled'
    try:
        if isinstance(total,(int,float)):
            total_fmt = f"{float(total):.2f}"
        else:
            total_fmt = str(total)
    except Exception:
        total_fmt = str(total)
    wrap.innerHTML = f'''
      <div class="bk-head">
        <div class="bk-hotel">
          <a href="/hotel/{escape_html(b.get('hotel_id'))}" class="bk-hotel-name">{escape_html(b.get('hotel_name') or 'Hotel')}</a>
          <div class="bk-dates">{fmt_date(b.get('check_in'))} → {fmt_date(b.get('check_out'))} <span class="nights">({nights} night{'s' if nights!=1 else ''})</span></div>
        </div>
        <div class="bk-meta">
          <span class="bk-status {status}</span>
          <span class="bk-total">${total_fmt}</span>
        </div>
      </div>
            <div class="bk-foot">
        <div class="bk-guests">Guests: {b.get('guests')}</div>
                <div class="bk-actions">{('<span class="bk-cancelled-note">—</span>' if cancelled else f'<button type="button" class="bk-cancel-btn" data-id="{escape_html(b.get('_id'))}">Cancel</button>')}</div>
      </div>
    '''
    if not cancelled:
        btn = wrap.querySelector('.bk-cancel-btn')
        if btn:
            # Pass the button element explicitly to avoid relying on evt.currentTarget
            btn.addEventListener('click', create_proxy(lambda evt, bid=b.get('_id'), w=wrap, be=btn: asyncio.ensure_future(cancel_booking(evt, bid, w, be))))
    return wrap

asyncio.ensure_future(load_bookings())

# footer years
try:
    from datetime import datetime
    document.getElementById('year').textContent = str(datetime.now().year)
    document.getElementById('p-year').textContent = str(datetime.now().year)
except Exception:
    pass
