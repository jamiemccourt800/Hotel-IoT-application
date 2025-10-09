from js import document, fetch
import asyncio, json, datetime

API_HOTELS = '/api/hotels'
API_CITIES = '/api/hotels/cities'

status_el = document.getElementById('status')
search_el = document.getElementById('search')
city_filter = document.getElementById('city-filter')
sort_filter = document.getElementById('sort-filter')
count_el = document.getElementById('result-count')
grid_el = document.getElementById('hotel-grid')
empty_el = document.getElementById('empty')
loading_el = document.getElementById('hotel-loading')

_all_hotels = []  # retained for minimal local filtering fallback
_active_fetch_id = 0
_debounce_handle = None

# Utility functions

def set_status(msg: str, kind: str = 'error'):
    if not status_el:
        return
    status_el.className = 'status-bar show ' + kind
    status_el.innerHTML = msg

def clear_status():
    if not status_el:
        return
    status_el.className = 'status-bar'
    status_el.innerHTML = ''

def render_hotels(data):
    if grid_el:
        grid_el.innerHTML = ''
    if empty_el:
        if not data:
            empty_el.style.display = 'block'
        else:
            empty_el.style.display = 'none'
    frag = document.createDocumentFragment()
    for h in data or []:
        card = document.createElement('div')
        card.className = 'hotel-card'
        hid = h.get('hotel_id','')
        link = f"/hotel/{hid}" if hid else '#'
        name = h.get('name','')
        city = h.get('city','')
        country = h.get('country','')
        price = h.get('price_per_night','')
        img = h.get('image','')
        card.innerHTML = f'''<div class="hotel-content" style="height: auto; min-height: 200px;">
            <picture><img loading="lazy" src="{img}" alt="{name}" style="height: 120px; object-fit: cover;" /></picture>
            <div class="hotel-body" style="padding: 8px;">
            <div class="hotel-name" style="font-size: 0.9rem; margin-bottom: 4px;">{name}</div>
            <div class="meta" style="font-size: 0.8rem; margin-bottom: 4px;">{city} • {country}</div>
            <div class="price" style="font-size: 0.85rem; margin-bottom: 6px;">€{price} <span style="font-size:.6rem; letter-spacing:.15em; opacity:.7; font-weight:500;">/ night</span></div>
            <button class="u-btn" style="padding: 4px 8px; font-size: 0.8rem;" onclick="window.location.href='{link}'">View details &rarr;</button>
            </div>
        </div>'''
        frag.appendChild(card)
    if grid_el:
        grid_el.appendChild(frag)
    if count_el:
        n = len(data or [])
        count_el.innerHTML = f"{n} result{'s' if n!=1 else ''}"

async def load_cities():
    # Load distinct cities from server
    try:
        if not city_filter:
            return
        resp = await fetch(API_CITIES)
        if not getattr(resp, 'ok', False):
            return
        data = await resp.json()
        py = data.to_py()
        cities = py.get('cities', [])
        # Clear existing except first (All Cities)
        while city_filter and city_filter.options.length > 1:
            city_filter.remove(1)
        for c in cities:
            opt = document.createElement('option')
            opt.value = c
            opt.textContent = c
            city_filter.appendChild(opt)
    except Exception:
        pass

def schedule_fetch():
    # Debounce typing (manual simple debounce via setTimeout)
    from js import window
    global _debounce_handle
    if _debounce_handle is not None:
        window.clearTimeout(_debounce_handle)
    def later():
        asyncio.ensure_future(remote_fetch())
    _debounce_handle = window.setTimeout(create_proxy(lambda *_: later()), 320)

async def remote_fetch():
    global _active_fetch_id, _all_hotels
    _active_fetch_id += 1
    fetch_id = _active_fetch_id
    term = (search_el.value.strip() if search_el else '')
    city = (city_filter.value if city_filter else '')
    sort = (sort_filter.value if sort_filter else '')
    params = []
    if term:
        params.append(f"q={term}")
    if city:
        params.append(f"city={city}")
    if sort:
        params.append(f"sort={sort}")
    qs = ("?" + "&".join(params)) if params else ''
    try:
        if loading_el:
            loading_el.style.display = 'flex'
        if grid_el:
            grid_el.style.opacity = '0.3'
        resp = await fetch(API_HOTELS + qs)
        ctype = resp.headers.get('Content-Type') if hasattr(resp, 'headers') else None
        if not ctype or 'application/json' not in ctype.lower():
            return
        data = await resp.json()
        py = data.to_py()
        if fetch_id != _active_fetch_id:
            # stale result
            return
        hotels = py.get('hotels', [])
        _all_hotels = hotels
        render_hotels(hotels)
    except Exception as e:
        set_status('Search failed: ' + str(e), 'error')
    finally:
        if loading_el:
            loading_el.style.display = 'none'
        if grid_el:
            grid_el.style.opacity = '1'

async def initial_load():
    clear_status()
    await load_cities()
    await remote_fetch()

# Event listeners
from pyodide.ffi import create_proxy
if search_el:
    search_el.addEventListener('input', create_proxy(lambda evt: schedule_fetch()))
if city_filter:
    city_filter.addEventListener('change', create_proxy(lambda evt: schedule_fetch()))
if sort_filter:
    sort_filter.addEventListener('change', create_proxy(lambda evt: schedule_fetch()))

# Kick off
asyncio.ensure_future(initial_load())

# Footer year
try:
    document.getElementById('year').innerHTML = str(datetime.datetime.now().year)
except Exception:
    pass
