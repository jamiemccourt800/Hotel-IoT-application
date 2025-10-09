from js import window, document, fetch, encodeURIComponent, console
import json, datetime, asyncio
from pyodide.ffi import create_proxy, create_once_callable

# hotel_id injected into template via data attribute on a container element
container = document.getElementById('hotel-detail')
hotel_id = container.getAttribute('data-hotel-id') if container else ''
API_DETAIL = f"/api/hotels/{hotel_id}"
API_BOOK = '/api/bookings'

status_el = document.getElementById('status')
wrapper = document.getElementById('hotel-detail')
skel = document.getElementById('loading-skel')
book_btn = document.getElementById('book-btn')
booking_status = document.getElementById('booking-status')

# ---------------- Utility -----------------

def set_status(msg, kind='error'):
    if not status_el: return
    status_el.className = f'status show {kind}'
    status_el.textContent = msg

def clear_status():
    if not status_el: return
    status_el.className = 'status'
    status_el.textContent = ''

# --------------- Detail Load --------------
async def load_detail():
    try:
        r = await fetch(API_DETAIL)
        # Attempt JSON parse guarded by content-type
        ctype = r.headers.get('Content-Type') if hasattr(r, 'headers') else ''
        if 'application/json' not in ctype.lower():
            set_status('Unexpected response while loading hotel', 'error')
            return
        data = await r.json()
        py = data.to_py()
        if not py.get('ok'):
            set_status(py.get('error','Failed to load'), 'error')
            return
        h = py.get('hotel', {})
        # Basic fields
        document.getElementById('hotel-name').textContent = h.get('name','')
        city = h.get('city','')
        country = h.get('country','')
        document.getElementById('hotel-location').textContent = f"{city} • {country}".strip()
        document.getElementById('hotel-price').textContent = f"${h.get('price_per_night',0)} / night"
        img = document.getElementById('hero-img')
        if img:
            img.src = h.get('image','')
            img.alt = h.get('name','')
        # Capacity / hint
        cap_el = document.getElementById('hotel-capacity')
        if cap_el:
            if 'room_count' in h:
                cap_el.textContent = f"Rooms: {h['room_count']}"
            elif 'capacity_hint' in h:
                cap_el.textContent = h['capacity_hint']
            else:
                cap_el.hidden = True
        # Managers
        mgrs = h.get('managers')
        mgr_el = document.getElementById('hotel-managers')
        if mgr_el:
            if mgrs:
                mgr_el.textContent = 'Managers: ' + ', '.join(mgrs)
            else:
                mgr_el.hidden = True
        # Created timestamp
        created_ts = h.get('created_at')
        created_el = document.getElementById('hotel-created')
        if created_el:
            if created_ts:
                try:
                    dt = datetime.datetime.utcfromtimestamp(int(created_ts))
                    created_el.textContent = 'Created ' + dt.strftime('%Y-%m-%d %H:%M UTC')
                except Exception:
                    created_el.hidden = True
            else:
                created_el.hidden = True
        # Reveal
        if skel: skel.hidden = True
        if wrapper: wrapper.hidden = False
        # Map embed
        try:
            if city or country:
                q = f"{city} {country}".strip()
                src = 'https://www.google.com/maps?q=' + encodeURIComponent(q) + '&output=embed'
                iframe = document.getElementById('hotel-map')
                ph = document.getElementById('map-placeholder')
                if iframe:
                    iframe.src = src
                    iframe.style.display = 'block'
                    if ph:
                        ph.textContent = 'Map loaded'
                        # IMPORTANT: when passing a Python callable to a JS API like setTimeout
                        # we must wrap it with create_once_callable/create_proxy so Pyodide
                        # keeps it alive for the duration of the callback. A raw lambda would
                        # create a temporary borrowed proxy which is destroyed at the end of
                        # the function, triggering the "borrowed proxy was automatically destroyed"
                        # error you observed in the console.
                        remove_cb = create_once_callable(lambda: ph.remove())
                        window.setTimeout(remove_cb, 1200)
        except Exception:
            pass
    except Exception as e:
        set_status(f'Error loading hotel: {e}', 'error')

# --------------- Booking ------------------

def set_booking_status(msg, kind='error'):
    if booking_status:
        booking_status.className = f'status show {kind}'
        booking_status.textContent = msg

def clear_booking_status():
    if booking_status:
        booking_status.className = 'status'
        booking_status.textContent = ''

async def do_booking(evt):
    evt.preventDefault()
    clear_booking_status()
    console.log('Starting booking process')
    
    if not book_btn:
        console.log('No book button found, returning')
        return
        
    ci_el = document.getElementById('check_in')
    co_el = document.getElementById('check_out')
    g_el  = document.getElementById('guests')
    ci = ci_el.value if ci_el else ''
    co = co_el.value if co_el else ''
    guests_raw = g_el.value if g_el else '1'
    
    console.log(f'Form values - check_in: {ci}, check_out: {co}, guests: {guests_raw}')
    
    if not ci or not co:
        console.log('Missing check-in or check-out dates')
        set_booking_status('Select check-in and check-out dates', 'error')
        return
    # Client-side date validation to match API: check_out must be after check_in
    try:
        ci_dt = datetime.date.fromisoformat(ci)
        co_dt = datetime.date.fromisoformat(co)
        if co_dt <= ci_dt:
            console.log('Invalid date range: check_out <= check_in')
            set_booking_status('Check-out must be after check-in', 'error')
            return
    except Exception as e:
        console.log(f'Date parse error: {e}')
        set_booking_status('Invalid date format', 'error')
        return

    # Guests must be a positive integer
    try:
        guests = int(guests_raw)
        if guests < 1:
            raise ValueError('guests')
    except Exception:
        console.log('Guests validation failed')
        set_booking_status('Guests must be a positive number', 'error')
        return
        
    payload = { 'hotel_id': hotel_id, 'check_in': ci, 'check_out': co, 'guests': guests }
    console.log(f'Booking payload: {payload}')
    
    try:
        book_btn.disabled = True
        book_btn.textContent = 'Booking...'
        console.log('Sending booking request...')
        
        r = await fetch(API_BOOK, {
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            'body': json.dumps(payload),
            'credentials': 'same-origin'
        })
        
        status = r.status
        console.log(f'Response status: {status}')
        
        ctype = r.headers.get('Content-Type') if hasattr(r, 'headers') else ''
        console.log(f'Response content-type: {ctype}')
        
        if 'application/json' in ctype.lower():
            data = await r.json()
            py = data.to_py()
            console.log(f'Response data: {py}')
            
            if status == 201 and py.get('ok'):
                bk = py.get('booking', {})
                total = bk.get('total_cost')
                console.log(f'Booking successful - total cost: {total}')
                
                try:
                    total_fmt = f"{float(total):.2f}"
                except Exception:
                    total_fmt = str(total)
                    
                set_booking_status(f"Booking confirmed • {bk.get('nights','?')} nights • Total ${total_fmt}", 'success')
                console.log('Redirecting to bookings page in 900ms')
                
                # Redirect to bookings page shortly so the user can see it saved
                def _redir():
                    window.location.href = '/bookings'
                window.setTimeout(_redir, 900)
            else:
                err = py.get('error','Booking failed')
                if status == 401:
                    err = 'Please login first to book.'
                console.log(f'Booking failed: {err}')
                set_booking_status(err, 'error')
        else:
            console.log('Non-JSON response received')
            if status == 401:
                set_booking_status('Please login to book this hotel.', 'error')
            elif status == 404:
                set_booking_status('Booking endpoint not found. Refresh page.', 'error')
            else:
                try:
                    txt = await r.text()
                    snippet = (txt[:120] + '…') if len(txt) > 120 else txt
                    console.log(f'Response text snippet: {snippet}')
                except Exception:
                    snippet = ''
                set_booking_status(f'Unexpected response ({status}): {snippet}', 'error')
    except Exception as e:
        console.log(f'Booking error: {e}')
        set_booking_status(f'Error: {e}', 'error')
    finally:
        console.log('Restoring book button state')
        book_btn.disabled = False
        book_btn.textContent = 'Book Now'

# --------------- Init ---------------------
form = document.getElementById('booking-form')
if form:
    form.addEventListener('submit', create_proxy(do_booking))
elif book_btn:
    book_btn.addEventListener('click', create_proxy(do_booking))

asyncio.ensure_future(load_detail())

# Footer year
try:
    document.getElementById('year').textContent = str(datetime.datetime.now().year)
except Exception:
    pass

# ----------- Date constraints (UX) -----------
try:
    ci_el = document.getElementById('check_in')
    co_el = document.getElementById('check_out')
    if ci_el and co_el:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        # Set minimum selectable dates
        ci_el.min = today.isoformat()
        co_el.min = tomorrow.isoformat()

        def on_ci_change(evt=None):
            try:
                new_ci = datetime.date.fromisoformat(ci_el.value) if ci_el.value else today
                new_min_co = new_ci + datetime.timedelta(days=1)
                co_el.min = new_min_co.isoformat()
                # Auto-correct invalid co
                if co_el.value:
                    cur_co = datetime.date.fromisoformat(co_el.value)
                    if cur_co <= new_ci:
                        co_el.value = new_min_co.isoformat()
            except Exception:
                # If parsing fails, keep current constraints
                pass

        ci_el.addEventListener('change', create_proxy(on_ci_change))
except Exception:
    # Non-fatal if date elements not present
    pass
